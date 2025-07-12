import asyncio
import json
import os
import argparse
import boto3
from pydantic import BaseModel, Field
from typing import List, Literal, Final, Optional
from crawl4ai.deep_crawling.scorers import KeywordRelevanceScorer
from crawl4ai import AsyncWebCrawler, LLMExtractionStrategy, LLMConfig, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.deep_crawling import BestFirstCrawlingStrategy
from crawl4ai.deep_crawling.filters import (
    FilterChain,
    DomainFilter,
    URLPatternFilter
)
from botocore.exceptions import ClientError
from dynaconf import Dynaconf


class Area(BaseModel):
    """Representa uma medida de área."""
    value: float | None = Field(None, description="O valor numérico da área.")
    unit: str = Field("m²", description="A unidade de medida, com 'm²' como padrão.")


class Location(BaseModel):
    """Dados de localização do imóvel."""
    address: str | None = Field(None, description="Nome da rua e número.")
    bairro: str | None = Field(None, description="Nome do bairro.")
    cidade: str | None = Field(None, description="Nome da cidade.")
    estado: str | None = Field(None, description="Sigla do estado (ex: SC, SP).")
    zipcode: str | None = Field(None, description="Código de Endereçamento Postal (CEP).")


class Proximities(BaseModel):
    """Descreve a proximidade do imóvel a vários pontos de interesse."""
    proximo_mercado: bool | None = Field(None, description="Se é próximo a mercado.")
    proximo_escola: bool | None = Field(None, description="Se é próximo a escola.")
    proximo_hospital: bool | None = Field(None, description="Se é próximo a hospital.")
    proximo_parque: bool | None = Field(None, description="Se é próximo a parque.")
    proximo_shopping: bool | None = Field(None, description="Se é próximo a shopping.")
    proximo_universidade: bool | None = Field(None, description="Se é próximo a universidade.")
    proximo_praia: bool | None = Field(None, description="Se é próximo à praia.")
    proximo_centro: bool | None = Field(None, description="Se é próximo ao centro ou no bairro Centro.")
    proximo_banco: bool | None = Field(None, description="Se é próximo a banco.")
    proximo_padaria: bool | None = Field(None, description="Se é próximo a padaria.")
    proximo_restaurantes: bool | None = Field(None, description="Se é próximo a restaurantes.")
    proximo_aeroporto: bool | None = Field(None, description="Se é próximo a aeroporto.")
    proximo_rodovia: bool | None = Field(None, description="Se é próximo a rodovia.")
    proximo_clinica_veterinaria: bool | None = Field(None, description="Se é próximo a clínica veterinária.")


class Attributes(BaseModel):
    """Dicionário de características e comodidades do imóvel e condomínio."""
    mobiliado: bool | None = Field(None, description="Indica se o imóvel está mobiliado.")
    semi_mobiliado: bool | None = Field(None, description="Indica se o imóvel está semi-mobiliado.")
    vazio: bool | None = Field(None, description="Indica se o imóvel está vazio.")
    na_planta: bool | None = Field(None, description="Indica se o imóvel está na planta.")
    reformado: bool | None = Field(None, description="Indica se o imóvel foi reformado.")
    salao_de_festas: bool | None = Field(None, description="Possui salão de festas.")
    piscina: bool | None = Field(None, description="Possui piscina.")
    academia: bool | None = Field(None, description="Possui academia/gym.")
    churrasqueira: bool | None = Field(None, description="Possui churrasqueira.")
    sacada: bool | None = Field(None, description="Possui sacada (não integrada).")
    elevador: bool | None = Field(None, description="Possui elevador.")
    seguranca: bool | None = Field(None, description="Possui sistema de segurança (portaria/câmeras).")
    porteiro: bool | None = Field(None, description="Possui porteiro (físico ou eletrônico).")
    area_de_lazer: bool | None = Field(None, description="Possui área de lazer comum.")
    condominio_fechado: bool | None = Field(None, description="É um condomínio fechado.")
    aceita_pets: bool | None = Field(None, description="Permite animais de estimação.")
    espaco_pet: bool | None = Field(None, description="Possui um espaço dedicado para pets.")
    cozinha_living_integrado: bool | None = Field(None, description="Cozinha e living são integrados.")
    ar_condicionado: bool | None = Field(None, description="Possui ar condicionado.")
    vista_para_mar: bool | None = Field(None, description="Possui vista para o mar.")
    piso_porcelanato: bool | None = Field(None, description="Possui piso de porcelanato.")
    piso_laminado: bool | None = Field(None, description="Possui piso laminado.")
    piso_vinilico: bool | None = Field(None, description="Possui piso vinílico.")
    medidor_indivial: bool | None = Field(None, description="Possui medidores individuais de água, luz ou gás.")
    horta: bool | None = Field(None, description="Possui horta comunitária ou privativa.")
    acessibilidade: bool | None = Field(None, description="Possui recursos de acessibilidade.")
    vaga_coberta: bool | None = Field(None, description="A vaga de garagem é coberta.")


class Property(BaseModel):
    """
    Representa a estrutura de dados de um Imóvel, com as proximidades separadas.
    """
    reference: str = Field(..., description="Referência única do anúncio (código interno). Ex: TE01202.")
    name: str = Field(..., description="Título principal do anúncio. Ex: 'Apartamento com 3 suítes'.")
    description: str | None = Field(None, description="Descrição completa do anúncio com formatação HTML.")
    
    operation: Literal["VENDA", "ALUGUEL", "TEMPORADA"] = Field(..., description="Tipo de operação do anúncio.")
    
    price: float | None = Field(None, description="Preço de venda do imóvel em reais, sem formatação.")
    rent_price: float | None = Field(None, description="Preço do aluguel mensal em reais, sem formatação.")
    condominio: float | None = Field(None, description="Valor mensal do condomínio em reais.")
    iptu: float | None = Field(None, description="Valor do IPTU.")
    iptu_period: Literal["MENSAL", "ANUAL"] | None = Field(None, description="Periodicidade do valor do IPTU.")

    tipo: str | None = Field(None, description="Tipo do imóvel. Ex: APARTAMENTO, CASA, TERRENO.")
    
    dormitorios: int | None = Field(None, description="Número total de quartos/dormitórios.")
    suites: int | None = Field(None, description="Número de suítes (quartos com banheiro).")
    banheiros: int | None = Field(None, description="Quantidade total de banheiros.")
    vagas: int | None = Field(None, description="Número de vagas de garagem.")
    
    area_util: Area | None = Field(default_factory=Area, description="Área útil ou privativa.")
    area_total: Area | None = Field(default_factory=Area, description="Área total (pode incluir áreas comuns).")
    area_construida: Area | None = Field(default_factory=Area, description="Área construída (para casas).")
    area_terreno: Area | None = Field(default_factory=Area, description="Área total do terreno (para casas/terrenos).")

    preco_medio_m2: float | None = Field(None, description="Preço médio por m² (calculado).")

    images: List[str] = Field(default_factory=list, description="Lista de URLs das imagens do imóvel.")
    
    # --- Modelos Aninhados ---
    location: Location = Field(default_factory=Location)
    attributes: Attributes = Field(default_factory=Attributes)
    proximities: Proximities = Field(default_factory=Proximities)


class DB:
    def __init__(self):
        check_local = os.environ.get("IS_LOCAL")
        if check_local is not None and check_local.lower() in ("1", "true"):
            print("DynamoDB LOCAL")
            self._dynamodb = boto3.resource("dynamodb",
                                            region_name=os.environ.get("AWS_REGION"),
                                            endpoint_url=os.environ.get("DYNAMO_ENDPOINT"))
        else:
            self._dynamodb = boto3.resource("dynamodb")
        self._table = None

    def exists(self, table_name):
        """
        Determines whether a table exists. As a side effect, stores the table in
        a member variable.

        :param table_name: The name of the table to check.
        :return: True when the table exists; otherwise, False.
        """
        try:
            table = self._dynamodb.Table(table_name)
            table.load()
            exists = True
        except ClientError as err:
            if err.response["Error"]["Code"] == "ResourceNotFoundException":
                exists = False
            else:
                print(
                    "Couldn't check for existence of %s. Here's why: %s: %s",
                    table_name,
                    err.response["Error"]["Code"],
                    err.response["Error"]["Message"],
                )
                raise
        else:
            self._table = table
        return exists

    def create_table(self, table_name):
        """
        Creates an Amazon DynamoDB table that can be used to store movie data.
        The table uses the release year of the movie as the partition key and the
        title as the sort key.

        :param table_name: The name of the table to create.
        :return: The newly created table.
        """
        try:
            print("Creating table", table_name)
            self._table = self._dynamodb.create_table(
                TableName=table_name,
                KeySchema=[
                    {"AttributeName": "name", "KeyType": "HASH"},  # Partition key
                    {"AttributeName": "title", "KeyType": "RANGE"},  # Sort key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "name", "AttributeType": "S"},
                    {"AttributeName": "title", "AttributeType": "S"},
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 1,
                    'WriteCapacityUnits': 1
                }
            )
            self._table.wait_until_exists()
        except ClientError as err:
            print(
                "Couldn't create table %s. Here's why: %s: %s",
                table_name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        except AttributeError as err:
            print("Fudeu", err)
        else:
            return self._table

    def add_item(self, item):
        try:
            self._table.put_item(Item=item)
        except ClientError as err:
            print("Couldn't add to table %s. %s", self._table, err)
            raise


class CrawlerEngine:
    def __init__(self, configuration: Dynaconf, db: Optional[DB] = None):
        self._config = configuration
        self._db = db
        browser_options: Final[list[str]] = [
            "--disable-gpu",
            "--single-process"
        ]
        self._browser_config = BrowserConfig(
            headless=True,
            verbose=True,
            extra_args=browser_options
        )
        domain_filter = DomainFilter(
            allowed_domains=self._config.get('allowed_domains', []),
            blocked_domains=self._config.get('blocked_domains', [])
        )
        url_filter = URLPatternFilter(patterns=self._config.get('filter_patterns', []))
        filter_chain = FilterChain([domain_filter, url_filter])

        scorer = KeywordRelevanceScorer(
            keywords=self._config.get("keywords", []),
            weight=self._config.get("weight", 0)
        )

        # LLM config
        api_token = os.environ.get('LLM_API_TOKEN') or self._config.llm.api_token
        llm_config = LLMConfig(provider=self._config.llm.provider, api_token=api_token)
        
        strategy = LLMExtractionStrategy(llm_config,
                                         schema=Property.model_json_schema(),  # JSON schema of the data model
                                         extraction_type="schema",  # Type of extraction to perform
                                         instruction=self._config.llm.prompt,
                                         input_format="markdown",  # Format of the input content
                                         verbose=True)    
        max_pages = self._config.get('max_pages')
        print("Max pages limit:", max_pages)
        self._crawler_run_config = CrawlerRunConfig(
            cache_mode=CacheMode.DISABLED,
            target_elements=self._config.get('target_elements', []),
            deep_crawl_strategy=BestFirstCrawlingStrategy(
                max_depth=self._config.max_depth,
                include_external=False,
                filter_chain=filter_chain,
                url_scorer=scorer,
                max_pages=max_pages,
            ),
            stream=True,
            extraction_strategy=strategy)

    async def run(self):
        print(f"Starting crawler {self._config.start_page}")
        async with AsyncWebCrawler(config=self._browser_config) as crawler:
            crawled = {}
            async for result in await crawler.arun(
                url=self._config.start_page,
                config=self._crawler_run_config
            ):
                if self._db is not None:
                    values = json.loads(result.extracted_content)
                    if values is None or len(values) == 0:
                        continue
                    item = dict(imobiliaria=self._config.name,
                                url=result.url,
                                **values[0])
                    self._db.add_item(item)
                try:
                    crawled[result.url] = json.loads(result.extracted_content)
                except TypeError as ex:
                    print(f"Error parsing: {result.url}", ex)
            return crawled


def handler(event, context):
    print("Processing event", event, "context", context)
    value = event.get('name')
    config_file = os.environ.get("CONFIG_FILE", "acrc.yaml")
    if value:
        config_file = f"{value}.yaml"
    lambda_config = Dynaconf(
        envvar_prefix=False,
        merge_enabled=True,
        settings_files=[
            "common.yaml",
            config_file
        ]
    )
    db = DB()
    exists: bool = db.exists(lambda_config.table_name)
    if not exists:
        db.create_table(lambda_config.table_name)

    loop = asyncio.get_event_loop()
    engine = CrawlerEngine(lambda_config, db=db)
    loop.run_until_complete(engine.run())
    print('Finished')
    return 'ok'


async def main(config: Dynaconf):
    engine = CrawlerEngine(config)
    return await engine.run()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-config-file", type=str, default="config/common.yaml")
    parser.add_argument("--config-file", type=str, default="config/conexao.yaml")
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

    items = asyncio.run(main(config))
    with open(params.output_file, 'w') as fp:
        json.dump(items, fp)
    print(f"Saved results to {params.output_file}")
