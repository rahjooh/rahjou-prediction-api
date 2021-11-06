import motor
import gridfs
import dill
import pymongo
from motor import MotorGridFSBucket

from common.common_utils import SingletonMixin


class MongoConnector(SingletonMixin):
    _conn_str: str
    _db_name: str
    _coll_name: str
    _client: motor.motor_tornado.MotorClient
    _gfs: gridfs.GridFS

    def __init__(self, conn_str: str, db_name: str, coll_name: str):
        self._conn_str = conn_str
        self._db_name = db_name
        self._coll_name = coll_name

    def _init_mongo_gfs(self):
        # self._gfs = gridfs.GridFS(self._db)
        self._gfs = MotorGridFSBucket(self._db)

    def _init_mongo_client(self):
        self._client = motor.motor_tornado.MotorClient(self._conn_str)
        self._db = self._client.get_database(self._db_name)

    def stop(self):
        pass

    def start(self):
        self._init_mongo_client()
        self._init_mongo_gfs()

    async def do_find_one(self, query):
        return await self._db[self._coll_name].find_one(
            query,
            sort=[('modifiedTime', pymongo.DESCENDING)]
        )

    async def get_pipeline(self, pickle_file_id):
        grid_out = await self._gfs.open_download_stream(pickle_file_id)
        contents = await grid_out.read()
        return dill.loads(contents)
