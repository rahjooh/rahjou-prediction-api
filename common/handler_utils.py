import logging
import tornado.log
from types import TracebackType
from typing import (
    Any,
    Awaitable,
    Dict,
    Optional,
    Type,
)
import traceback
import uuid
import tornado.web
from scipy.sparse import csr_matrix
from tornado_prometheus import MetricsHandler  # type : ignore
import json
import numpy as np
from common import log_utils
from prediction_service.service import BaseService
import tornado


class NumpyScipyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, csr_matrix):
            return str(obj)
        return json.JSONEncoder.default(self, obj)


def do_projection(dic, projection_list):
    result = {}
    for key in projection_list:
        try:
            result[key] = dic[key]
        except KeyError as e:
            raise e

    return result


def un_flatt(dic):
    result_dict = dict()
    for key, value in dic.items():
        parts = key.split(".")
        d = result_dict
        for part in parts[:-1]:
            if part not in d:
                d[part] = dict()
            d = d[part]
        d[parts[-1]] = value

    return result_dict


class BaseRequestHandler(tornado.web.RequestHandler):
    service: BaseService
    config: Dict
    logger: logging.Logger

    # def data_received(self, chunk: bytes) -> Optional[Awaitable[None]]:
    #     pass

    def initialize(
            self,
            service: BaseService,
            config: Dict,
            logger: logging.Logger
    ) -> None:
        self.service = service
        self.config = config
        self.logger = logger

    def prepare(self) -> Optional[Awaitable[None]]:
        req_id = uuid.uuid4().hex
        log_utils.set_log_context(
            req_id=req_id,
            method=self.request.method,
            uri=self.request.uri,
            ip=self.request.remote_ip
        )

        log_utils.log(
            self.logger,
            logging.DEBUG,
            include_context=True,
            message='REQUEST'
        )

        return super().prepare()

    def on_finish(self) -> None:
        super().on_finish()

    def write_error(self, status_code: int, **kwargs: Any) -> None:
        self.set_header('Content-Type', 'application/json; charset=UTF-8')
        body = {
            'method': self.request.method,
            'uri': self.request.path,
            'code': status_code,
            'message': self._reason
        }

        log_utils.set_log_context(reason=self._reason)

        if 'exc_info' in kwargs:
            exc_info = kwargs['exc_info']
            log_utils.set_log_context(exc_info=exc_info)
            if self.settings.get('serve_traceback'):
                # in debug mode, send a traceback
                trace = '\n'.join(traceback.format_exception(*exc_info))
                body['trace'] = trace

        self.finish(body)

    def log_exception(
            self,
            typ: Optional[Type[BaseException]],
            value: Optional[BaseException],
            tb: Optional[TracebackType],
    ) -> None:
        # https://www.tornadoweb.org/en/stable/web.html#tornado.web.RequestHandler.log_exception
        if isinstance(value, tornado.web.HTTPError):
            if value.log_message:
                msg = value.log_message % value.args
                log_utils.log(
                    tornado.log.gen_log,
                    logging.WARNING,
                    status=value.status_code,
                    request_summary=self._request_summary(),
                    message=msg
                )
        else:
            log_utils.log(
                tornado.log.app_log,
                logging.ERROR,
                message='Uncaught exception',
                request_summary=self._request_summary(),
                request=repr(self.request),
                exc_info=(typ, value, tb)
            )


class DefaultRequestHandler(BaseRequestHandler):
    def initialize(  # type: ignore
            self,
            status_code: int,
            message: str,
            logger: logging.Logger
    ):
        self.logger = logger
        self.set_status(status_code, reason=message)

    def prepare(self) -> Optional[Awaitable[None]]:
        raise tornado.web.HTTPError(
            self._status_code,
            'request uri: %s',
            self.request.uri,
            reason=self._reason
        )


class MetricsPageHandler(BaseRequestHandler, MetricsHandler):
    pass
