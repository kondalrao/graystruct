============
 graystruct
============

Integration between structlog and graylog GELF, provided by graypy.


Rationale
=========

Structlog_ provides a rich tool for producing structured log messages
from applications.  Graypy_ provides a Python interface to emit logs in
the GELF_ format accepted by graylog_.  In effect, structlog_
pre-processes the _inputs_ to Python ``logging`` module, while graypy_
processes the outputs (``LogRecord`` instances), and neither expects the
other to be present.

``graystruct`` provides a small integration layer composed of two main
components that are used in conjunction with both structlog_ and
graypy_.  These components minimally alter the behaviour of structlog_
and graypy_ at their interface points so that they are able to cooperate
in producing structured logs.


Example
=======


.. code-block:: python

    >>> import logging
    >>> import structlog
    >>> from graystruct.encoder import GELFEncoder
    >>> from graystruct.handler import GELFHandler
    >>> from graystruct.rabbitmq import GELFRabbitHandler
    >>> from graystruct.utils import add_app_context
    >>> structlog.configure(
    ...     logger_factory=structlog.stdlib.LoggerFactory(),
    ...     processors=[
    ...         # Prevent exception formatting if logging is not configured
    ...         structlog.stdlib.filter_by_level,
    ...         # Add file, line, function information of where log occurred
    ...         add_app_context,
    ...         # Format positional args to log as in stdlib
    ...         structlog.stdlib.PositionalArgumentsFormatter(),
    ...         # Add a timestamp to log message
    ...         structlog.processors.TimeStamper(utc=True),
    ...         # Dump stack if ``stack_info=True`` passed to log
    ...         structlog.processors.StackInfoRenderer(),
    ...         # Format exception info is ``exc_info`` passed to log
    ...         structlog.processors.format_exc_info,
    ...         # Encode the message in GELF format (this must be the final processor)
    ...         GELFEncoder(),
    ...     ],
    ... )
    >>> std_logger = logging.getLogger()
    >>> std_logger.setLevel(logging.WARNING)
    >>> gelf_handler = GELFHandler('localhost', 12201)
    >>> std_logger.addHandler(gelf_handler)
    >>> rabbit_handler = GELFRabbitHandler(
            'amqp://user:passwd@localhost/', exchange='log-exchange',
            queue='log-queue')
    >>> std_logger.addHandler(rabbit_handler)
    >>> logger = structlog.get_logger('some.package')
    # Will transmit a GELF-encoded message directly to a graylog server and to rabbitmq
    >>> logger.error('user.login', username='sjagoe')


Notes on RabbitMQ handler
-------------------------

The ``GELFRabbitHandler`` will declare the exchange that it is
submitting messages to.  The consumer is expected to create a queue
binding to the exchange when receiving messages.  If the consumer does
not, at least one queue binding should be made by the RabbitMQ server
administrator in order for log messages to be delivered.


.. _structlog: https://pypi.python.org/pypi/structlog
.. _Structlog: https://pypi.python.org/pypi/structlog

.. _graypy: https://pypi.python.org/pypi/graypy
.. _Graypy: https://pypi.python.org/pypi/graypy

.. _graylog: https://www.graylog.org
.. _GELF: https://www.graylog.org/resources/gelf-2/
