from marshmallow import Schema, fields, validate


class BaseSchema(Schema):
    class Meta:
        ordered = True


class AppActivitySchema(BaseSchema):
    lastSessionTime = fields.Int(required=True)
    totalDuration = fields.Int(required=True)
    totalDurationRecent = fields.Int(required=True)
    sessionCount = fields.Int(required=True)
    sessionCountRecent = fields.Int(required=True)


class AppFeaturesInstallSchema(BaseSchema):
    index = fields.Int(required=True)
    installations = fields.Int(required=True)


class AppFeaturesActivitySchema(BaseSchema):
    index = fields.Int(required=True)
    appActivity = fields.Nested(AppActivitySchema, required=True)


class AppGroupActivityFeaturesSchema(AppFeaturesActivitySchema):
    pass


class AppGenreActivityFeaturesSchema(AppFeaturesActivitySchema):
    pass


class AppGroupInstallFeaturesSchema(AppFeaturesInstallSchema):
    pass


class AppGenreInstallFeaturesSchema(AppFeaturesInstallSchema):
    pass


class BaseCountSchema(BaseSchema):
    count = fields.Int(required=True)
    recentCount = fields.Int(required=True)
    lastTime = fields.Int(required=True)


class BaseSearchCountSchema(BaseSchema):
    index = fields.Int(required=True)
    searchCount = fields.Int(required=True)
    searchCountRecent = fields.Int(required=True)
    lastTime = fields.Int(required=True)


class ImpressionsSchema(BaseCountSchema):
    pass


class ClicksSchema(BaseCountSchema):
    pass


class InstallsSchema(BaseCountSchema):
    pass


class BaseActivitySchema(BaseSchema):
    impressions = fields.Nested(
        ImpressionsSchema,
        required=True,
    )
    clicks = fields.Nested(
        ClicksSchema,
        required=True,
    )
    installs = fields.Nested(
        InstallsSchema,
        required=True,
    )


class BannerActivitySchema(BaseActivitySchema):
    pass


class VideoActivitySchema(BaseActivitySchema):
    pass


class SearchActivitySchema(BaseActivitySchema):
    pass


class AdFeaturesSchema(BaseSchema):
    index = fields.Int(required=True)
    bannerActivity = fields.Nested(
        BannerActivitySchema,
        required=True,
    )
    videoActivity = fields.Nested(
        VideoActivitySchema,
        required=True,
    )
    searchActivity = fields.Nested(
        SearchActivitySchema,
        required=True,
    )


class AdGroupFeaturesSchema(AdFeaturesSchema):
    pass


class AdGenreFeaturesSchema(AdFeaturesSchema):
    pass


class AdHistoryFeatureSchema(BaseSchema):
    adFeatures = fields.Nested(AdFeaturesSchema, many=True, required=True)
    adGroupFeatures = fields.Nested(AdGroupFeaturesSchema, many=True, required=True)
    adGenreFeatures = fields.Nested(AdGenreFeaturesSchema, many=True, required=True)


class QueryGroupFeaturesSchema(BaseSearchCountSchema):
    pass


class QueryGenreFeaturesSchema(BaseSearchCountSchema):
    pass


class SearchHistoryFeatureSchema(BaseSchema):
    queryFeatures = fields.Nested(
        BaseSearchCountSchema,
        required=True,
        many=True
    )
    queryGroupFeatures = fields.Nested(
        QueryGroupFeaturesSchema,
        required=True,
        many=True
    )
    queryGenreFeatures = fields.Nested(
        QueryGenreFeaturesSchema,
        required=True,
        many=True,
    )


class ContextSchema(BaseSchema):
    zoneId = fields.Int(
        required=True
    )
    zoneType = fields.Int(
        required=True,
        example=2,
        validate=validate.Range(min=0, max=3)
    )
    dayOfWeek = fields.Int(
        required=True,
        example=2,
        validate=validate.Range(min=0, max=6)
    )
    hourOfDay = fields.Int(
        required=True,
        example=2,
        validate=validate.Range(min=0, max=23)
    )
    device = fields.Int(
        required=True,
        example=2, validate=validate.Range(min=0, max=4))
    contentGenre = fields.Int(required=True)


class AppHistoryActivityFeatureSchema(BaseSchema):
    appFeatures = fields.Nested(AppFeaturesActivitySchema, many=True, required=True)
    appGroupFeatures = fields.Nested(AppGroupActivityFeaturesSchema, many=True, required=True)
    appGenreFeatures = fields.Nested(AppGenreActivityFeaturesSchema, many=True, required=True)


class AppHistoryInstallFeatureSchema(BaseSchema):
    appFeatures = fields.Nested(AppFeaturesInstallSchema, many=True, required=True)
    appGroupFeatures = fields.Nested(AppGroupInstallFeaturesSchema, many=True, required=True)
    appGenreFeatures = fields.Nested(AppGenreInstallFeaturesSchema, many=True, required=True)


class UserProfileSchema(BaseSchema):
    appHistoryActivityFeature = fields.Nested(
        AppHistoryActivityFeatureSchema,
        required=True
    )

    appHistoryInstallFeature = fields.Nested(
        AppHistoryInstallFeatureSchema,
        required=True
    )

    adHistoryFeature = fields.Nested(
        AdHistoryFeatureSchema,
        required=True
    )

    searchHistoryFeature = fields.Nested(
        SearchHistoryFeatureSchema,
        required=True
    )


class PredictInputDataSchema(BaseSchema):
    userPegahId = fields.Str(required=False)
    context = fields.Nested(  # type: ignore
        ContextSchema,
        required=True,
    )
    userProfile = fields.Nested(
        UserProfileSchema,
        required=True
    )


class CreativeFuture(BaseSchema):
    creativeId = fields.Int(required=True)
    creativeIdIndex = fields.Int(required=True)
    adPackageName = fields.Int(required=True)
    adGenre = fields.Int(required=True)
    adGroup = fields.Int(required=True)
    incomeType = fields.Int(required=True)
    bidType = fields.Int(required=True)
    trendWeighted = fields.Int(required=True)
    growthWeighted = fields.Int(required=True)


class PredictRequestSchema(BaseSchema):
    request = fields.Nested(
        PredictInputDataSchema,
        required=True,
    )
    creatives = fields.Nested(
        CreativeFuture,
        many=True,
        required=True,
    )


class PredictResponseSchema(BaseSchema):
    creativeId = fields.Int(required=True)
    cvr = fields.Float(required=True)
