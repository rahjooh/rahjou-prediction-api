from typing import (
    Mapping,
    Dict
)
import logging

from tornado.gen import multi

from adapters.mongo_connector import MongoConnector
from common.common_utils import SingletonMixin


class BaseService(SingletonMixin):
    config: Mapping
    logger: logging.Logger

    def __init__(self, config, logger) -> None:
        self.config = config
        self.logger = logger


class PredictionService(BaseService):
    mongo: MongoConnector

    def __init__(self, config: Mapping, logger: logging.Logger, mongo) -> None:
        self.mongo = mongo
        super().__init__(config, logger)

    @classmethod
    async def transform(cls, col_data, pipeline) -> Dict:
        r = await pipeline.transform(col_data)
        return r

    @classmethod
    async def parallel_batch_predict(cls, col_data_list, pipeline):
        return await multi(
            list(map(lambda col_data:
                     cls.transform(col_data, pipeline),
                     col_data_list)
                 )
        )

    @classmethod
    def stop(cls):
        pass

    @classmethod
    def start(cls):
        pass
