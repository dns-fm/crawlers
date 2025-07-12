from pydantic import BaseModel


class CrawlerResult(BaseModel):
    name: str
    url: str
    content: str
