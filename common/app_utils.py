import logging

import swagger_ui
import tornado.web
from tornado_prometheus import PrometheusMixIn
from adapters.mongo_connector import MongoConnector
from common.handler_utils import DefaultRequestHandler
from common.log_utils import log_function
from prediction_service.service import PredictionService
from scripts.generate_swagger_file import generate_swagger_file
from urls import get_app_urls
from typing import (
    Dict,
    Tuple
)


class BaseApp(PrometheusMixIn, tornado.web.Application):
    pass


def make_prediction_app(
        config: Dict,
        debug: bool,
        logger: logging.Logger,
        mongo: MongoConnector,
        port: str
) -> Tuple[PredictionService, tornado.web.Application]:
    service = PredictionService(config, logger, mongo)
    urls = get_app_urls(service=service, config=config, logger=logger)
    generate_swagger_file(urls, './swagger.json', port)
    app = BaseApp(
        urls,
        compress_response=True,  # compress textual responses
        log_function=log_function,  # log_request() uses it to log results
        serve_traceback=debug,  # it is passed on as setting to write_error()
        default_handler_class=DefaultRequestHandler,
        default_handler_args={
            'status_code': 404,
            'message': 'Unknown Endpoint',
            'logger': logger
        }
    )
    swagger_ui.tornado_api_doc(
        app,
        config_path='./swagger.json',
        url_prefix="/swagger/spec.html",
        title="Prediction API",
    )

    return service, app
