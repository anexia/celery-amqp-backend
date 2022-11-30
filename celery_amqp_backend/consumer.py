import socket
import time

import kombu

from celery.backends import asynchronous

__all__ = [
    'DirectReplyAMQPResultConsumer',
]


class DirectReplyAMQPResultConsumer(asynchronous.BaseResultConsumer):
    Consumer = kombu.Consumer

    _consumers = {}
    _channels = {}

    def __init__(self, *args, **kwargs):
        print("#####################################")
        print("INIT: DirectReplyAMQPResultConsumer")
        print("#####################################")

        super().__init__(*args, **kwargs)

        self._create_binding = self.backend._create_binding

    def on_state_change(self, meta, message):
        print("#####################################")
        print("ON_STATE_CHANGE: DirectReplyAMQPResultConsumer")
        print("#####################################")

        self.backend._set_cache_by_message(meta['task_id'], message)

        return super().on_state_change(meta, message)

    def start(self, task_id, channel=None, **kwargs):
        if not channel:
            raise RuntimeError(f"DirectReplyAMQPResultConsumer missing channel for {task_id!r}")

        self._channels[task_id] = channel

        if id(channel) not in self._consumers:
            consumer = self._consumers[id(channel)] = self.Consumer(
                channel or self.app.connection().default_channel,
                [
                    self._create_binding(task_id),
                ],
                callbacks=[
                    self.on_state_change
                ],
                no_ack=True,
                auto_declare=True,
                accept=self.accept,
            )
            consumer.consume()

        print("#####################################")
        print("START: DirectReplyAMQPResultConsumer")
        print("#####################################")

    def drain_events(self, timeout=None):
        print("#####################################")
        print("DRAIN_EVENTS: DirectReplyAMQPResultConsumer")
        print("#####################################")

        if self._consumers:
            for consumer in self._consumers.values():
                try:
                    consumer.connection.drain_events(timeout=timeout)
                except socket.timeout:
                    pass
        elif timeout:
            time.sleep(timeout)

    def stop(self):
        for consumer in self._consumers.values():
            try:
                consumer.cancel()
            finally:
                consumer.connection.close()

        print("#####################################")
        print("STOP: DirectReplyAMQPResultConsumer")
        print("#####################################")

    def on_after_fork(self):
        print("#####################################")
        print("ON_AFTER_FORK: DirectReplyAMQPResultConsumer")
        print("#####################################")

        if self._consumers:
            for consumer in self._consumers.values():
                consumer.connection.collect()
            self._consumers.clear()

    def channel_for(self, task_id):
        return self._channels.get(task_id)

    def consumer_for(self, task_id):
        channel_id = self._channels.get(task_id)
        return self._consumers[id(channel_id)]

    def consume_from(self, task_id):
        pass

    def cancel_for(self, task_id):
        pass
