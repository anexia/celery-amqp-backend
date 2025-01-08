import collections
import kombu
import socket

from celery import states
from celery.backends import base

from .exceptions import *


__all__ = [
    "AMQPBackend",
]


class AMQPBackend(base.BaseBackend):
    """
    Celery result backend that creates a temporary queue for each result of a task. This backend is more or less a
    re-implementation for the old AMQP result backend.
    """

    READY_STATES = states.READY_STATES
    PROPAGATE_STATES = states.PROPAGATE_STATES

    Exchange = kombu.Exchange
    Consumer = kombu.Consumer
    Producer = kombu.Producer
    Queue = kombu.Queue

    BacklogLimitExceededException = AMQPBacklogLimitExceededException
    WaitEmptyException = AMQPWaitEmptyException
    WaitTimeoutException = AMQPWaitTimeoutException

    persistent = True
    supports_autoexpire = True
    supports_native_join = True

    retry_policy = {
        "max_retries": 20,
        "interval_start": 0,
        "interval_step": 1,
        "interval_max": 1,
    }

    def __init__(
        self,
        app,
        exchange=None,
        exchange_type=None,
        persistent=None,
        serializer=None,
        auto_delete=True,
        **kwargs,
    ):
        super().__init__(app, **kwargs)

        conf = self.app.conf

        self.persistent = self.prepare_persistent(persistent)
        self.delivery_mode = 2 if self.persistent else 1
        self.result_exchange = exchange or conf.result_exchange or "celery_result"
        self.result_exchange_type = (
            exchange_type or conf.result_exchange_type or "direct"
        )
        self.exchange = self._create_exchange(
            self.result_exchange,
            self.result_exchange_type,
            self.delivery_mode,
        )
        self.serializer = serializer or conf.result_serializer
        self.auto_delete = auto_delete

    def store_result(
        self,
        task_id,
        result,
        state,
        traceback=None,
        request=None,
        **kwargs,
    ):
        """
        Sends the task result for the given task identifier to the task result queue and returns the sent result dict.

        :param task_id: Task identifier to send the result for
        :param result: The task result as dict
        :param state: The task result state
        :param traceback: The traceback if the task resulted in an exception
        :param request: Request data
        :param kwargs:
        :return: The task result as dict
        """
        # Determine the routing key and a potential correlation identifier. We use the task identifier as
        # correlation identifier as a fallback.
        routing_key, correlation_id = (
            self._create_routing_key(task_id),
            request and request.correlation_id or task_id,
        )

        with self.app.amqp.producer_pool.acquire(block=True) as producer:
            producer.publish(
                {
                    "task_id": task_id,
                    "status": state,
                    "result": self.encode_result(result, state),
                    "traceback": traceback,
                    "children": self.current_task_children(request),
                },
                exchange=self.exchange,
                routing_key=routing_key,
                correlation_id=correlation_id,
                serializer=self.serializer,
                retry=True,
                retry_policy=self.retry_policy,
                declare=[
                    self._create_binding(task_id),
                ],
                delivery_mode=self.delivery_mode,
            )

        return result

    def wait_for(
        self,
        task_id,
        timeout=None,
        cache=True,
        no_ack=True,
        on_message=None,
        on_interval=None,
        **kwargs,
    ):
        """
        Gets a single task result from the queue. The messages may come from the cache or may be consumed from the
        queue itself. This method returns the task result data as a dict and may raise an exception if a result
        contains an exception message.

        :param task_id: The task identifiers we want the result for
        :param timeout: Consumer read timeout
        :param no_ack: If enabled the messages are automatically acknowledged by the broker
        :param cache: Make use of the result backend cache
        :param on_message: Callback function for received messages
        :param on_interval: Callback function for message poll intervals
        :param kwargs:
        :return: Task result body as dict
        """
        for fetched_task_id, fetched_task_result in self.get_many(
            [
                task_id,
            ],
            timeout=timeout,
            no_ack=no_ack,
            cache=cache,
            on_interval=on_interval,
        ):
            return fetched_task_result

        raise self.WaitEmptyException(task=task_id)

    def get_many(
        self,
        task_ids,
        timeout=None,
        no_ack=True,
        cache=True,
        on_message=None,
        on_interval=None,
        **kwargs,
    ):
        """
        Gets multiple task results from the queue. The messages may come from the cache or may be consumed from the
        queue itself. This method returns an iterator for tuples of task identifier and task results and may raise
        an exception if a result contains an exception message.

        :param task_ids: List of task identifiers we want the result for
        :param timeout: Consumer read timeout
        :param no_ack: If enabled the messages are automatically acknowledged by the broker
        :param cache: Make use of the result backend cache
        :param on_message: Callback function for received messages
        :param on_interval: Callback function for message poll intervals
        :param kwargs:
        :return: Iterator for received task identifier and task result body
        """
        task_ids = set(task_ids)
        cached_task_ids = set()
        mark_cached = cached_task_ids.add
        get_cached = self._cache.get

        # First we try to get the desired task results from the cache and yield the values.
        if cache:
            for task_id in task_ids:
                cached_task_result = get_cached(task_id)
                if (
                    cached_task_result
                    and cached_task_result["status"] in self.READY_STATES
                ):
                    yield task_id, cached_task_result
                    mark_cached(task_id)

        # As we may have already yielded some task results from the cache, we remove those task identifiers from
        # the list of desired task results we want to drain from the queue. If there are no desired task results
        # left, we return.
        task_ids.difference_update(cached_task_ids)
        if not task_ids:
            return

        with self.app.pool.acquire_channel(block=True) as (conn, channel):
            # We are going to drain messages from the queue. To process the results, we push the task results we get
            # from the messages to the `results` collection and yield those task results.
            results = collections.deque()
            push_result = results.append
            push_cache = self._cache.__setitem__
            decode_result = self.meta_from_decoded
            wait = conn.drain_events
            next_task_result = results.popleft

            def on_message_callback(message):
                """
                Callback function that gets called for every message we receive from the queue. This function
                processes the messages, and puts the results to the `results` collection. The task result gets pushed
                to the result backend cache too.

                :param message: Message drained from the queue
                :return:
                """
                # Decode and process the message a task result.
                received_task_result = decode_result(message.decode())

                # If there is a callback function for received messages, we trigger the callback now.
                if on_message is not None:
                    on_message(received_task_result)

                received_task_state, received_task_id = (
                    received_task_result["status"],
                    received_task_result["task_id"],
                )

                # If the task result is ready, we push it to the result cache. If the task result is als a result
                # for a task we are looking for, we push the result to the `results` collection to yield it afterwards.
                if received_task_state in self.READY_STATES:
                    push_cache(received_task_id, received_task_result)

                    if received_task_id in task_ids:
                        push_result(received_task_result)

            # Create the queue bindings for the tasks we want the results for.
            bindings = self._create_many_bindings(task_ids)

            with self.Consumer(
                channel,
                bindings,
                on_message=on_message_callback,
                accept=self.accept,
                no_ack=no_ack,
            ):
                # Drain task results from the bindings as long as there are tasks left whose result we did
                # not yield yet.
                while task_ids:
                    # Drain messages from the connection.
                    try:
                        wait(timeout=timeout)
                    except socket.timeout:
                        raise self.WaitTimeoutException()

                    while results:
                        task_result = next_task_result()
                        task_id = task_result["task_id"]
                        task_ids.discard(task_id)
                        yield task_id, task_result

                    # If there is a callback function for polling intervals, we trigger the callback now.
                    if on_interval is not None:
                        on_interval()

    def get_task_meta(self, task_id, backlog_limit=1000):
        """
        Gets the task meta without removing the task from the queue. To do so, this method task result messages from
        the queue, and sends the latest task result message back to the queue. As this result backend does not keep
        the history of task results, older task result messages get acknowledged and thus removed from the queue.

        :param task_id: The task we want to get the result meta for
        :param backlog_limit: Limits how often we fetch a message from the result queue to get the latest one
        :return: Result meta as dict
        """
        with self.app.pool.acquire_channel(block=True) as (_, channel):
            # First we bind to the queue and declare the queue to make sure it exists and that we can read
            # from it later on.
            binding = self._create_binding(task_id)(channel)
            binding.declare()

            prev = latest = None

            # As we will get the oldest messages from the queue first, we read until we have found the latest
            # message or util we reached the limit of read tries.
            for i in range(backlog_limit):
                # Get a pending message from the queue.
                current = binding.get(
                    accept=self.accept,
                    no_ack=False,
                )

                # If there are no more pending messages on the queue, we have found the latest message and can
                # break the loop now.
                if not current:
                    break

                # We make sure that the task result message we got is for the task we are interested in. As we declare
                # a separate result queue for each task, there should not be any messages for other tasks, but better
                # be safe than sorry.
                if current.payload["task_id"] == task_id:
                    prev, latest = latest, current

                if prev:
                    # This result backend is not expected to keep the history of task results, so we delete everything
                    # except the most recent task result.
                    prev.ack()
                    prev = None
            else:
                raise self.BacklogLimitExceededException(task=task_id)

            # If we got a latest task result from the queue, we store this message to the local cache, send the task
            # result message back to the queue, and return it. Else, we try to get the task result from the local
            # cache, and assume that the task result is pending if it is not present on the cache.
            if latest:
                payload = self._cache[task_id] = self.meta_from_decoded(latest.payload)
                latest.requeue()
                return payload
            else:
                try:
                    return self._cache[task_id]
                except KeyError:
                    return {
                        "status": states.PENDING,
                        "result": None,
                    }

    def as_uri(self, include_password=True):
        """
        Gets the URL representation of the result backend.

        :param include_password: Include passwords for the backend (unused for this backend)
        :return: Backend URL representation
        """
        return "{}.{}://".format(
            self.__class__.__module__,
            self.__class__.__qualname__,
        )

    def reload_task_result(self, task_id):
        raise NotImplementedError(
            "reload_task_result is not supported by this backend.",
        )

    def reload_group_result(self, task_id):
        raise NotImplementedError(
            "reload_group_result is not supported by this backend.",
        )

    def save_group(self, group_id, result):
        raise NotImplementedError("save_group is not supported by this backend.")

    def restore_group(self, group_id, cache=True):
        raise NotImplementedError("restore_group is not supported by this backend.")

    def delete_group(self, group_id):
        raise NotImplementedError("delete_group is not supported by this backend.")

    def add_to_chord(self, chord_id, result):
        raise NotImplementedError("add_to_chord is not supported by this backend.")

    def _forget(self, task_id):
        pass

    def _create_exchange(self, name, exchange_type="direct", delivery_mode=2):
        """
        Creates an exchange with the given parameters.

        :param name: Name of the exchange as string
        :param exchange_type: Type of the exchange as string (e.g. 'direct', 'topic', …)
        :param delivery_mode: Exchange delivery mode as integer (1 for transient, 2 for persistent)
        :return: Created exchange
        """
        return self.Exchange(
            name=name,
            type=exchange_type,
            delivery_mode=delivery_mode,
            durable=self.persistent,
            auto_delete=False,
        )

    def _create_binding(self, task_id):
        """
        Creates a queue binding for the given task identifier.

        :param task_id: Task identifier as string
        :return: Created binding
        """
        name = self._create_routing_key(task_id)
        return self.Queue(
            name=name,
            exchange=self.exchange,
            routing_key=name,
            durable=self.persistent,
            auto_delete=self.auto_delete,
            expires=self.expires,
        )

    def _create_many_bindings(self, task_ids):
        """
        Creates queue bindings for the given list of task identifiers.

        :param task_ids: List of task identifiers
        :return: List of created bindings
        """
        return [self._create_binding(task_id) for task_id in task_ids]

    def _create_routing_key(self, task_id):
        """
        Creates a routing key from the given task identifier. The resulting routing key will consist of the
        exchange name as well as the task identifier.

        :param task_id: Task identifier as string
        :return: Routing key as string
        """
        return f"{self.result_exchange}.{task_id}"

    def __reduce__(self, args=(), kwargs=None):
        kwargs = kwargs if kwargs else {}
        kwargs.update(
            url=self.url,
            exchange=self.exchange.name,
            exchange_type=self.exchange.type,
            persistent=self.persistent,
            serializer=self.serializer,
            auto_delete=self.auto_delete,
            expires=self.expires,
        )
        return super().__reduce__(args, kwargs)
