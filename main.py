import asyncio
import os
import json
import argparse
from crawl4ai import AsyncWebCrawler, LLMExtractionStrategy, LLMConfig, BrowserConfig, CrawlerRunConfig, CacheMode, SemaphoreDispatcher, RateLimiter
from pydantic import BaseModel
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import (
    FilterChain,
    DomainFilter,
    URLPatternFilter,
    ContentTypeFilter
)
from dynaconf import Dynaconf

class Area(BaseModel):
    value: float
    unit: str

class Property(BaseModel):
    """
    Represents the data structure of a Property.
    """
    reference: str
    name: str
    price: float
    condominio: float
    iptu: float
    operation: str
    cidade: str
    bairro: str
    zipcode: str
    address: str
    tipo: str
    description: str
    images: list[str]
    suites: int
    dormitorios: int
    vagas: int 
    area_total: Area
    area_util: Area
    area_contruida: Area
    area_terreno: Area
    attributes: dict[str, str | int | list[str] | bool]

class CrawlerEngine:
    def __init__(self, config: Dynaconf):
        self.config = config
        self._browser_config = BrowserConfig(headless=True)
        domain_filter = DomainFilter(
            allowed_domains=config.get('allowed_domains', []),
            blocked_domains=config.get('blocked_domains', [])
        )
        url_filter = URLPatternFilter(patterns=config.get('filter_patterns', []))
        filter_chain = FilterChain([domain_filter, url_filter])

        # LLM config
        llm_config = LLMConfig(provider=config.llm.provider, api_token=config.llm.api_key)
        
        strategy = LLMExtractionStrategy(llm_config,
                                         schema=Property.model_json_schema(),  # JSON schema of the data model
                                         extraction_type="schema",  # Type of extraction to perform
                                         instruction=config.llm.prompt,
                                         input_format="markdown",  # Format of the input content
                                         verbose=True)    

        self._crawler_run_config = CrawlerRunConfig(
            cache_mode=CacheMode.BYPASS,
            target_elements=config.get('target_elements', []),
            deep_crawl_strategy=BestFirstCrawlingStrategy(
                max_depth=config.max_depth, 
                include_external=False,
                filter_chain=filter_chain,
                max_pages=config.max_pages,
            ),
            extraction_strategy=strategy)

    async def run(self):
        async with AsyncWebCrawler(config=self._browser_config) as crawler:
            results = await crawler.arun(
                url=self.config.start_page,
                config=self._crawler_run_config
            )
            crawled = {}
            for result in results:
                crawled[result.url] = json.loads(result.extracted_content)
            return crawled

async def main(config: Dynaconf, output_file: str):
    engine = CrawlerEngine(config)
    items = await engine.run()
    with open(output_file, 'w') as fp:
        json.dump(items, fp)
    print(f"Saved results to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-config-file", type=str, default="common.yaml")
    parser.add_argument("--config-file", type=str, default="acrc.yaml")
    parser.add_argument("--output-file", type=str, default="imoveis.json")
    params = parser.parse_args()

    print(f"Running crawler with {params.config_file}")
    config = Dynaconf(
        envvar_prefix="",
        merge_enabled=True,
        settings_files=[
           params.base_config_file,
           params.config_file
        ]
    )

    asyncio.run(main(config, params.output_file))
