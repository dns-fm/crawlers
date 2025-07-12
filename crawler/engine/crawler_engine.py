import os
import re
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
        api_token = os.environ.get('LLM_API_TOKEN') or self._config.llm.api_token
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
                extraction_strategy=self._extraction_strategy
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

        crawler_run_config = CrawlerRunConfig(
            deep_crawl_strategy=BestFirstCrawlingStrategy(
                max_depth=self._config.max_depth,
                include_external=False,
                filter_chain=filter_chain
            )
        )

        links = set()
        results = await crawler.arun(url=self._config.start_page,
                                     config=crawler_run_config)
        for result in results:
            for link in result.links['internal']:
                url = link['href']
                if self._item_url_pattern.match(url):
                    links.add(url)
        return list(links)

