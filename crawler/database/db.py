from abc import ABCMeta, abstractmethod
from crawler.models.crawler_result import CrawlerResult


class DB(metaclass=ABCMeta):

    @abstractmethod
    def add_item(self, item: CrawlerResult):
        pass
