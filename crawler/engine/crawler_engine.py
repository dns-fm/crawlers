import os
import re
import jinja2
from crawl4ai import (
    AsyncWebCrawler,
    LLMExtractionStrategy,
    LLMConfig,
    BrowserConfig,
    CrawlerRunConfig,
    BestFirstCrawlingStrategy,
)
from crawl4ai.deep_crawling.filters import (
    FilterChain,
    DomainFilter,
    URLPatternFilter,
    ContentTypeFilter
)
from dynaconf import Dynaconf
from crawler.models.property import Property
from crawler.database.db import DB
from crawler.models.crawler_result import CrawlerResult


class CrawlerEngine:
    def __init__(self, configuration: Dynaconf, db: DB):
        self._config = configuration
        self._db = db
        self._browser_config = BrowserConfig(
            headless=True,
            verbose=True,
        )
        self._item_url_pattern = re.compile(self._config.items_url_pattern)
        api_token = os.environ.get('LLM_API_TOKEN')
        llm_config = LLMConfig(provider=self._config.llm.provider,
                               api_token=api_token)

        self._extraction_strategy = LLMExtractionStrategy(llm_config,
                                                          schema=Property.model_json_schema(),
                                                          extraction_type="schema",
                                                          instruction=self._config.llm.prompt,
                                                          input_format="markdown",
                                                          verbose=True)

    async def run(self) -> None:
        print(f"Starting crawler {self._config.name}")
        total = 0
        async with AsyncWebCrawler(config=self._browser_config) as crawler:
            urls: list[str] = await self._get_urls(crawler)
            crawler_run_config = CrawlerRunConfig(
                target_elements=self._config.get("target_elements", []),
                stream=True,
                mean_delay=0.5,
                max_range=0.8,
                # TODO: add LLM
                # extraction_strategy=self._extraction_strategy
            )
            async for result in await crawler.arun_many(urls=urls,
                                                        config=crawler_run_config):
                crawler_result = CrawlerResult(name=self._config.name,
                                               url=result.url,
                                               content=result.markdown)
                if crawler_result.name is not None and crawler_result.url is not None:
                    self._db.add_item(crawler_result)
                total += 1
        print(f"Total de páginas inseridas {total}. Imobiliária {self._config.name}")

    async def _get_urls(self, crawler: AsyncWebCrawler) -> list[str]:
        filter_chain = FilterChain([
            # Only follow URLs with specific patterns
            URLPatternFilter(patterns=self._config.get("filter_patterns", [])),

            # Only crawl specific domains
            DomainFilter(
                allowed_domains=self._config.get("allowed_domains", []),
                blocked_domains=self._config.get("blocked_domains", [])
            ),
            # Only include specific content types
            ContentTypeFilter(allowed_types=["text/html"])
        ])

        if self._config.get('next_pages'):
            pages = []
            template = jinja2.Environment().from_string(self._config.next_pages.pattern)
            for current_page in range(1, self._config.next_pages.max_pages + 1):
                pages.append(template.render(page=current_page))
            urls = list(set([self._config.start_page] + pages))
            crawl = crawler.arun_many(urls=urls, config=CrawlerRunConfig(stream=True))
        else:
            crawler_run_config = CrawlerRunConfig(
                stream=True,
                deep_crawl_strategy=BestFirstCrawlingStrategy(
                    max_depth=self._config.max_depth,
                    include_external=False,
                    filter_chain=filter_chain
                )
            )
            crawl = crawler.arun(url=self._config.start_page, config=crawler_run_config)

        links = set()
        async for result in await crawl:
            for link in result.links.get('internal', []):
                url = link['href']
                if self._item_url_pattern.match(url):
                    links.add(url)
        return list(links)

