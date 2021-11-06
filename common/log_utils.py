import aiotask_context as context  # type: ignore
import logfmt  # type: ignore
import logging
import re
import traceback
from typing import Dict

import tornado.web

from prediction_service import LOGGER_NAME

LOG_CONTEXT = 'log_context'


def get_log_context() -> Dict:
    log_context = context.get(LOG_CONTEXT)
    if log_context is None:
        log_context = {}
        context.set(LOG_CONTEXT, log_context)

    return log_context


def set_log_context(**kwargs) -> None:
    log_context = get_log_context()
    log_context.update(kwargs)


def clear_log_context() -> None:
    log_context = get_log_context()
    log_context.clear()


def log(
    logger: logging.Logger,
    lvl: int,
    include_context: bool = False,
    **kwargs
) -> None:

    all_info = {**get_log_context(), **kwargs} if include_context else kwargs

    info = {
        k: v for k, v in all_info.items()
        if k not in ['exc_info', 'stack_info', 'extra']
    }

    exc_info = all_info.get('exc_info')
    # stack_info = all_info.get('stack_info', False)
    # extra = all_info.get('extra', {})

    if exc_info:  # (typ, value, tb)
        trace = '\t'.join(traceback.format_exception(*exc_info))
        info['trace'] = re.sub(r'[\r\n]+', '\t', trace)

    msg = next(logfmt.format(info))
    logger.log(
        lvl, msg,
        # exc_info=exc_info, stack_info=stack_info, extra=extra
    )


def log_function(handler: tornado.web.RequestHandler) -> None:
    # https://www.tornadoweb.org/en/stable/web.html#tornado.web.Application.settings

    logger = getattr(handler, 'logger', logging.getLogger(LOGGER_NAME))
    if handler.get_status() < 400:
        level = logging.INFO
    elif handler.get_status() < 500:
        level = logging.WARNING
    else:
        level = logging.ERROR

    log(
        logger,
        level,
        include_context=True,
        message='RESPONSE',
        status=handler.get_status(),
        time_ms=(1000.0 * handler.request.request_time())
    )
    clear_log_context()
