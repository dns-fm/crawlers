import pytz
from pydantic import BaseModel, Field
from crawler.models.property import Property
from datetime import datetime

tz = pytz.timezone("America/Sao_Paulo")


class CrawlerResult(BaseModel):
    name: str
    url: str
    markdown: str
    property: Property
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=tz))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(tz=tz))
