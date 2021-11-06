import tornado.web
import json
from marshmallow import ValidationError

from api.schemas import PredictRequestSchema
from common.handler_utils import (
    BaseRequestHandler,
)
from prediction_service.models import ColData, CafeBazaarPipeLine
from prediction_service.service import PredictionService


class CafeBazaarPredictionRequestHandler(BaseRequestHandler):
    service: PredictionService

    async def post(self):
        """Returns all cvr estimations
                ---
                tags: [CVR ESTIM]
                summary: Get cvr es
                description: Get all cvres

                requestBody:
                    description: Prediction API requestBody
                    required: True
                    content:
                        application/json:
                            schema:
                                PredictRequestSchema


                responses:
                    200:
                        description: List of cvr est
                        content:
                            application/json:
                                schema:
                                    type: array
                                    items:
                                        PredictResponseSchema

                """
        try:
            data = json.loads(self.request.body)
        
            predict_request_body = PredictRequestSchema().load(data=data)
            del data

        except ValidationError as e:
            raise tornado.web.HTTPError(
                400, reason=str(e.messages)
            )
        except (json.decoder.JSONDecodeError, TypeError):
            raise tornado.web.HTTPError(
                400, reason='Invalid JSON body'
            )
        except ValueError as e:
            raise tornado.web.HTTPError(400, reason=str(e))

        try:
            pipeline = await CafeBazaarPipeLine(self.service.mongo).load()
            columns = pipeline.getRequiredColnames()

            predict_request_body_col_data_format = await ColData(
                predict_request_body, columns).load()
            del predict_request_body

            pipeline.transform(predict_request_body_col_data_format)

            result = []
            for c, y_pred in list(
                    zip(
                        predict_request_body_col_data_format["creativeId"].tolist(),
                        predict_request_body_col_data_format["estimatedCVR"].tolist()
                    )
            ):
                result.append({"creativeId": c, "cvr": y_pred})

            result = json.dumps(
                result,
            )
            self.set_header('Content-Type', 'application/json')
            self.set_status(201)
            await self.finish(result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise tornado.web.HTTPError(
                500, reason=str(e)
            )
