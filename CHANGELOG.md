# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2024-10-25
### Added
- Added support for Celery 5.4

### Removed
- Removed support for Python 3.8

## [1.1.0] - 2023-11-03
### Added
- Added support for Python 3.11 and Python 3.12
- Added support for Celery 5.2 and 5.3

### Removed
- Removed support for Python 3.6 and Python 3.7
- Removed support for Celery 5.0 and 5.1

### Fixed
- Queues not cleaned up after an `AMQPWaitTimeoutException`

## [1.0.0] - 2021-10-19
### Added
- AMQP result backend for Celery

[Unreleased]: https://github.com/anexia/celery-amqp-backend/compare/1.2.0...HEAD
[1.2.0]: https://github.com/anexia/celery-amqp-backend/releases/tag/1.2.0
[1.1.0]: https://github.com/anexia/celery-amqp-backend/releases/tag/1.1.0
[1.0.0]: https://github.com/anexia/celery-amqp-backend/releases/tag/1.0.0
