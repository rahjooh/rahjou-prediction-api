import copy
from typing import Dict
import numpy as np
import scipy as sp
import collections
from aiocache import cached, Cache

from adapters.mongo_connector import MongoConnector
from common.common_utils import SingletonMixin

NUM_APPS = 1000
NUM_QUERIES = 1000
NUM_APP_GROUPS = 30
NUM_APP_GENRES = 30
NUM_QUERY_CATEGORIES = 30
NUM_ADS = 1000


class SparseTmp():
    def __init__(self, shape, dtype):
        self.rows = []
        self.cols = []
        self.vals = []
        self.dtype = dtype
        self.shape = shape

    def __setitem__(self, key, val):
        self.rows.append(key[0])
        self.cols.append(key[1])
        self.vals.append(val)

    #         pass
    #         print(key,' --- ',val)

    def toSklearn(self, targetConstructor=sp.sparse.csr_matrix):
        return targetConstructor((self.vals, (self.rows, self.cols)), shape=self.shape, dtype=self.dtype)

    def tocsr(self):
        return self.toSklearn(sp.sparse.csr_matrix)

    def repeat_rows(self):  # repeat col values to fill all the row with the same values
        N = self.shape[0]
        m = len(self.rows)

        self.rows = [i for i in range(N) for j in range(m)]
        self.cols = self.cols * N
        self.vals = self.vals * N


class ColData:
    def __init__(self, json_format: Dict, columns: list) -> None:

        self.json_format = json_format
        self.N = len(self.json_format.get('creatives'))  # type: ignore
        self.required_cols = columns
        sparse_mat_constructor = SparseTmp  # sp.sparse.dok_matrix
        col_data = {}

        # Action
        col_data['incomeType'] = np.zeros(self.N, np.uint8)
        col_data['bidType'] = np.zeros(self.N, np.uint8)

        # AdInfo
        for col_name in ['creativeId', 'adPackageName', 'adGenre', 'adGroup', 'creativeIdIndex']:
            col_data[col_name] = np.zeros(self.N, np.uint16)

        # Context
        for col_name in ['zoneType', 'dayOfWeek', 'hourOfDay', 'device', 'zoneId', 'contentGenre', 'trendWeighted',
                         'growthWeighted']:
            col_data[col_name] = np.zeros(self.N, np.uint8)

        # UserAppHist
        col_data['userAppHist'] = collections.defaultdict(dict)
        col_data['userAppHist']['installed'] = sparse_mat_constructor((self.N, NUM_APPS), dtype=np.bool)
        for time_stat in ['lastTime', 'totalDuration', 'totalDurationRecent']:
            col_data['userAppHist']['activityLevel'][time_stat] = sparse_mat_constructor((self.N, NUM_APPS),
                                                                                         dtype=np.uint64)
        for constant in ['sessionCount', 'sessionCountRecent']:
            col_data['userAppHist']['activityLevel'][constant] = sparse_mat_constructor((self.N, NUM_APPS),
                                                                                        dtype=np.uint16)

        # UserAppGroupHist
        col_data['userAppGroupHist'] = collections.defaultdict(dict)
        col_data['userAppGroupHist']['installed'] = sparse_mat_constructor((self.N, NUM_APP_GROUPS), dtype=np.uint8)
        for time_stat in ['lastTime', 'totalDuration', 'totalDurationRecent']:
            col_data['userAppGroupHist']['activityLevel'][time_stat] = sparse_mat_constructor((self.N, NUM_APP_GROUPS),
                                                                                              dtype=np.uint64)
        for constant in ['sessionCount', 'sessionCountRecent']:
            col_data['userAppGroupHist']['activityLevel'][constant] = sparse_mat_constructor((self.N, NUM_APP_GROUPS),
                                                                                             dtype=np.uint16)

        # UserAppGenreHist
        col_data['userAppGenreHist'] = collections.defaultdict(dict)
        col_data['userAppGenreHist']['installed'] = sparse_mat_constructor((self.N, NUM_APP_GENRES), dtype=np.uint8)
        for time_stat in ['lastTime', 'totalDuration', 'totalDurationRecent']:
            col_data['userAppGenreHist']['activityLevel'][time_stat] = sparse_mat_constructor((self.N, NUM_APP_GENRES),
                                                                                              dtype=np.uint64)
        for constant in ['sessionCount', 'sessionCountRecent']:
            col_data['userAppGenreHist']['activityLevel'][constant] = sparse_mat_constructor((self.N, NUM_APP_GENRES),
                                                                                             dtype=np.uint16)

        # UserSearchHist
        col_data['userSearchHist'] = collections.defaultdict(dict)
        col_data['userSearchHist']['count'] = sparse_mat_constructor((self.N, NUM_QUERIES), dtype=np.uint8)
        col_data['userSearchHist']['recentCount'] = sparse_mat_constructor((self.N, NUM_QUERIES), dtype=np.uint8)
        col_data['userSearchHist']['lastTime'] = sparse_mat_constructor((self.N, NUM_QUERIES), dtype=np.uint64)

        # UserSearchCategoryHist
        col_data['userSearchCategoryHist'] = collections.defaultdict(dict)
        col_data['userSearchCategoryHist']['count'] = sparse_mat_constructor((self.N, NUM_QUERY_CATEGORIES),
                                                                             dtype=np.uint8)
        col_data['userSearchCategoryHist']['recentCount'] = sparse_mat_constructor((self.N, NUM_QUERY_CATEGORIES),
                                                                                   dtype=np.uint8)
        col_data['userSearchCategoryHist']['lastTime'] = sparse_mat_constructor((self.N, NUM_QUERY_CATEGORIES),
                                                                                dtype=np.uint64)

        # UserAdHist
        col_data['userAdHist'] = collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(dict)))
        for adHistZoneType in ['banner', 'video', 'search']:
            for action in ['impression', 'click', 'install']:
                col_data['userAdHist'][adHistZoneType][action]['count'] = sparse_mat_constructor((self.N, NUM_ADS),
                                                                                                 dtype=np.uint8)
                col_data['userAdHist'][adHistZoneType][action]['recentCount'] = sparse_mat_constructor(
                    (self.N, NUM_ADS),
                    dtype=np.uint8)
                col_data['userAdHist'][adHistZoneType][action]['lastTime'] = sparse_mat_constructor((self.N, NUM_ADS),
                                                                                                    dtype=np.uint64)

        # UserAdGroupHist
        col_data['userAdGroupHist'] = collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(dict)))
        for adHistZoneType in ['banner', 'video', 'search']:
            for action in ['impression', 'click', 'install']:
                col_data['userAdGroupHist'][adHistZoneType][action]['count'] = sparse_mat_constructor(
                    (self.N, NUM_APP_GROUPS),
                    dtype=np.uint8)
                col_data['userAdGroupHist'][adHistZoneType][action]['recentCount'] = sparse_mat_constructor(
                    (self.N, NUM_APP_GROUPS), dtype=np.uint8)
                col_data['userAdGroupHist'][adHistZoneType][action]['lastTime'] = sparse_mat_constructor(
                    (self.N, NUM_APP_GROUPS), dtype=np.uint64)

        # UserAdGenreHist
        col_data['userAdGenreHist'] = collections.defaultdict(
            lambda: collections.defaultdict(lambda: collections.defaultdict(dict)))
        for adHistZoneType in ['banner', 'video', 'search']:
            for action in ['impression', 'click', 'install']:
                col_data['userAdGenreHist'][adHistZoneType][action]['count'] = sparse_mat_constructor(
                    (self.N, NUM_APP_GENRES),
                    dtype=np.uint8)
                col_data['userAdGenreHist'][adHistZoneType][action]['recentCount'] = sparse_mat_constructor(
                    (self.N, NUM_APP_GENRES), dtype=np.uint8)
                col_data['userAdGenreHist'][adHistZoneType][action]['lastTime'] = sparse_mat_constructor(
                    (self.N, NUM_APP_GENRES), dtype=np.uint64)

        self.data = ColData._flatten(
            col_data,
            atom_check_func=lambda x: isinstance(x, sp.sparse.base.spmatrix) or isinstance(x, SparseTmp)
        )

    def _clear_from_json_data(self) -> None:
        self.json_format.clear()

    @staticmethod
    def _is_sparse_matrix_json(d):
        return all(
            [
                isinstance(key, np.number) or
                isinstance(key, int)
                for key in d
            ]
        )

    @staticmethod
    def _flatten(d, parent_key='', sep='.', atom_check_func=None):
        """
        d: input dictionary.
        sep: the separator used between parent and child in making keys.
        atom_check_func: a function which checks an input and returns true
        if it should be considered as an atom and not be flattened.
        """

        if atom_check_func is None:
            def atom_check_func():
                return False

        if atom_check_func(d):
            return d

        items = []
        if isinstance(d, list):
            d = {str(i): d[i] for i in range(len(d))}
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if (
                    isinstance(v, collections.MutableMapping) or
                    isinstance(v, list)
            ) and not atom_check_func(v):
                items.extend(
                    ColData._flatten(
                        v,
                        new_key,
                        sep=sep,
                        atom_check_func=atom_check_func
                    ).items())
            else:
                items.append((new_key, v))

        return dict(items)

    def bulk_insert_to_col_data(self, base_input, N, key, val):

        if isinstance(self.data[key], sp.sparse.base.spmatrix):
            val = base_input.get(key, {})
            for dim, dimval in val.items():
                if dimval > 0:
                    i = 0
                    while N - i > 0:
                        if i == 0:
                            self.data[key][i, dim] = dimval
                        else:
                            self.data[key][i, dim].fill(self.data[key][0, dim])
                        i += 1
        else:
            val = base_input[key]
            i = 0
            while N - i > 0:
                self.data[key][i].fill(val)
                i += 1

    def insert_to_col_data(self, sample, key, val, i):
        if isinstance(self.data[key], sp.sparse.base.spmatrix) or isinstance(self.data[key], SparseTmp):
            val = sample.get(key, {})
            for dim, dimval in val.items():
                if dimval > 0:
                    self.data[key][i, dim] = dimval
        else:
            val = sample[key]
            self.data[key][i] = val

    def load_base_mlaas_input(self, base_sample):
        base_input = {
            "userAppHist": {
                "installed": {},
                "activityLevel": {
                    "lastTime": {},
                    "totalDuration": {},
                    "totalDurationRecent": {},
                    "sessionCount": {},
                    "sessionCountRecent": {}
                },
            },
            "userSearchHist": {
                "count": {},
                "recentCount": {},
                "lastTime": {}
            },
            "userAdHist": {
                "banner": {
                    "impression": {
                        "count": {},
                        "recentCount": {},
                        "lastTime": {}
                    },
                    "click": {
                        "count": {},
                        "recentCount": {},
                        "lastTime": {}
                    },
                    "install": {
                        "count": {},
                        "recentCount": {},
                        "lastTime": {}
                    }
                },
                "video": {},
                "search": {}
            }

        }
        base_input["userAppGroupHist"] = copy.deepcopy(base_input["userAppHist"])
        base_input["userAppGenreHist"] = copy.deepcopy(base_input["userAppHist"])
        base_input["userSearchCategoryHist"] = copy.deepcopy(base_input["userSearchHist"])
        base_input["userAdHist"]["video"] = copy.deepcopy(base_input["userAdHist"]["banner"])
        base_input["userAdHist"]["search"] = copy.deepcopy(base_input["userAdHist"]["banner"])
        base_input["userAdGenreHist"] = copy.deepcopy(base_input["userAdHist"])
        base_input["userAdGroupHist"] = copy.deepcopy(base_input["userAdHist"])

        for k, v in base_sample.get("context", {}).items():
            base_input[k] = v

        for app_features, k in [
            (base_sample["userProfile"]["appHistoryInstallFeature"]["appFeatures"], "userAppHist"),
            (base_sample["userProfile"]["appHistoryInstallFeature"]["appGenreFeatures"], "userAppGenreHist"),
            (base_sample["userProfile"]["appHistoryInstallFeature"]["appGroupFeatures"], "userAppGroupHist")
        ]:
            for app_feature in app_features:
                base_input[k]["installed"][app_feature["index"]] = app_feature["installations"]

        for app_features, k in [
            (base_sample["userProfile"]["appHistoryActivityFeature"]["appFeatures"], "userAppHist"),
            (base_sample["userProfile"]["appHistoryActivityFeature"]["appGenreFeatures"], "userAppGenreHist"),
            (base_sample["userProfile"]["appHistoryActivityFeature"]["appGroupFeatures"], "userAppGroupHist")
        ]:
            for app_feature in app_features:
                base_input[k]["activityLevel"]["lastTime"][app_feature["index"]] = app_feature["appActivity"][
                    "lastSessionTime"]
                base_input[k]["activityLevel"]["totalDuration"][app_feature["index"]] = app_feature["appActivity"][
                    "totalDuration"]
                base_input[k]["activityLevel"]["totalDurationRecent"][app_feature["index"]] = \
                    app_feature["appActivity"][
                        "totalDurationRecent"]
                base_input[k]["activityLevel"]["sessionCount"][app_feature["index"]] = app_feature["appActivity"][
                    "sessionCount"]
                base_input[k]["activityLevel"]["sessionCountRecent"][app_feature["index"]] = app_feature["appActivity"][
                    "sessionCountRecent"]

        for ad_features, k in [
            (base_sample["userProfile"]["adHistoryFeature"]["adFeatures"], "userAdHist"),
            (base_sample["userProfile"]["adHistoryFeature"]["adGenreFeatures"], "userAdGenreHist"),
            (base_sample["userProfile"]["adHistoryFeature"]["adGroupFeatures"], "userAdGroupHist")
        ]:
            for ad_feature in ad_features:
                for t, k2 in [("banner", "bannerActivity"), ("video", "videoActivity"), ("search", "searchActivity")]:
                    for t2, k3 in [("impression", "impressions"), ("click", "clicks"), ("install", "installs")]:
                        base_input[k][t][t2]["count"][ad_feature["index"]] = ad_feature[k2][k3]["count"]
                        base_input[k][t][t2]["recentCount"][ad_feature["index"]] = ad_feature[k2][k3]["recentCount"]
                        base_input[k][t][t2]["lastTime"][ad_feature["index"]] = ad_feature[k2][k3]["lastTime"]

        for query_features, k in [
            (base_sample["userProfile"]["searchHistoryFeature"]["queryFeatures"], "userSearchHist"),
            (base_sample["userProfile"]["searchHistoryFeature"]["queryGenreFeatures"], "userSearchCategoryHist"),
        ]:
            for query_feature in query_features:
                base_input[k]["count"][query_feature["index"]] = query_feature["searchCount"]
                base_input[k]["recentCount"][query_feature["index"]] = query_feature["searchCountRecent"]
                base_input[k]["lastTime"][query_feature["index"]] = query_feature["lastTime"]

        return base_input

    async def load(self) -> Dict:
        base_sample = self.json_format['request']

        # %%timeit
        base_sample_legacy = self.load_base_mlaas_input(base_sample)

        flatten_base_sample = self._flatten(
            d=base_sample_legacy,  # type: ignore
            atom_check_func=self._is_sparse_matrix_json
        )

        # Insert shared data to first row
        for colname in flatten_base_sample:
            if colname in self.required_cols:
                self.insert_to_col_data(flatten_base_sample, colname, None, 0)

        # Repeat firstrow to other rows
        for colname in flatten_base_sample:
            if colname in self.required_cols:
                if isinstance(self.data[colname], SparseTmp):
                    self.data[colname].repeat_rows()
                else:
                    self.data[colname].fill(self.data[colname][0])

        # Fill not shared data
        for i, creative in enumerate(self.json_format['creatives']):
            for colname in creative:
                if colname in self.required_cols:
                    self.insert_to_col_data(creative, colname, None, i)

        for colname in self.data:
            if colname in self.required_cols:
                if isinstance(self.data[colname], sp.sparse.base.spmatrix) or isinstance(self.data[colname], SparseTmp):
                    self.data[colname] = self.data[colname].tocsr()

        return self.data


class PipeLineBase(SingletonMixin):
    _mongo: MongoConnector
    _document: Dict

    def __init__(self, mongo):
        self._mongo = mongo

    async def transform(self, col_data):
        t = self.pickle_file.transform(col_data)
        return await t


class CafeBazaarPipeLine(PipeLineBase):
    def __init__(self, mongo):
        self.tags = ['CafeVideo']
        super().__init__(mongo)

    @cached(ttl=3600, cache=Cache.MEMORY, key='CafeVideo')
    async def load(self):
        self._document = await self._mongo.do_find_one({'tags': self.tags})
        # self._document = await self._mongo.do_find_one({'_id': ObjectId('5fa656e6b4903de2d7ec2751')})
        grid_fs_link = self._document['definition']['stages'][0]['GridFsLink']
        pickle_file_id = grid_fs_link['pickleFileId']
        self.pickle_file = await self._mongo.get_pipeline(pickle_file_id)
        return self.pickle_file
