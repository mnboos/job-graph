from ninja import ModelSchema, Schema
from ninja.orm import register_field

from core.models import JobOpening

register_field("PointField", tuple)


class GeometrySchema(Schema):
    """Defines the geographical point of the feature."""

    type: str = "Point"
    coordinates: list[
        float
    ]  # Represents [longitude, latitude], tuple[float, float] would be better, but openapi-generator generates that as Array<any>


class PropertiesSchema(Schema):
    """
    Defines the descriptive properties of a feature.

    We only include fields the frontend needs, plus our custom `show_canton` flag.
    """

    name: str
    city: str | None = None
    state: str = None
    countrycode: str = None

    # This is the crucial field our backend logic adds.
    # It instructs the frontend on whether to display the canton for disambiguation.
    show_canton: bool


class PlacesSearchResult(Schema):
    """Represents a single, augmented search result feature."""

    type: str = "Feature"
    properties: PropertiesSchema
    geometry: GeometrySchema


class IsoPolygon(Schema):
    rings: list[
        list[list[float]]
    ]  # actually i'd prefer tuple[float,float] instead of list[float], but openapi-generator generates that as Array<any>


class IsochroneOut(Schema):
    polygons: list[IsoPolygon]


class JobOpeningOut(ModelSchema):
    id: int
    location: list[float] = None

    class Meta:
        model = JobOpening
        fields = ["id", "title", "company_name", "location", "description", "address", "city"]


class Point(Schema):
    lat: float
    lon: float


class DistanceCalculation(Schema):
    job_id: int
    abfahrtsort: Point
    profile: str
