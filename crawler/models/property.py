from pydantic import BaseModel, Field
from typing import List, Literal


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
