import type { AssetClass, SourceKind } from "./portal-data";

export interface CategorySource {
  source: Exclude<SourceKind, "unavailable">;
  badge: string;
  provider: string;
  coverage: string;
  cadence: string;
  detail: string;
}

export const categorySources: Record<AssetClass, CategorySource> = {
  acoes: { source: "official", badge: "Fechamento B3", provider: "B3 COTAHIST", coverage: "Fechamentos B3", cadence: "Por pregão", detail: "Preço de fechamento oficial e data de referência do arquivo COTAHIST." },
  fiis: { source: "official", badge: "Fechamento B3", provider: "B3 COTAHIST", coverage: "Fechamentos B3", cadence: "Por pregão", detail: "Preço de fechamento oficial e data de referência do arquivo COTAHIST." },
  etfs: { source: "official", badge: "Fechamento B3", provider: "B3 COTAHIST", coverage: "Fechamentos B3", cadence: "Por pregão", detail: "Preço de fechamento oficial e data de referência do arquivo COTAHIST." },
  bdrs: { source: "official", badge: "Fechamento B3", provider: "B3 COTAHIST", coverage: "Fechamentos B3", cadence: "Por pregão", detail: "Preço de fechamento oficial e data de referência do arquivo COTAHIST." },
  stocks: { source: "reference", badge: "Feed de mercado", provider: "Yahoo Finance", coverage: "Cotações globais", cadence: "Conforme o feed", detail: "Preços de referência do feed público, com possível atraso identificado pela fonte." },
  reits: { source: "reference", badge: "Feed de mercado", provider: "Yahoo Finance", coverage: "Cotações globais", cadence: "Conforme o feed", detail: "Preços de referência do feed público, com possível atraso identificado pela fonte." },
  cripto: { source: "real-time", badge: "Tempo real", provider: "Binance Spot", coverage: "Pares negociados", cadence: "Em tempo real", detail: "Fluxo de negociação da Binance; preço específico dessa corretora." },
  "renda-fixa": { source: "official", badge: "Fonte oficial", provider: "Banco Central do Brasil", coverage: "Taxas de referência", cadence: "Diária", detail: "Séries públicas do Banco Central, apresentadas com data de referência." },
  "tesouro-direto": { source: "official", badge: "Fonte oficial", provider: "Tesouro Transparente", coverage: "Preços e taxas", cadence: "Diária", detail: "Arquivo oficial de preços e taxas ofertadas pelo Tesouro Direto." },
  fiagros: { source: "official", badge: "Fechamento B3", provider: "B3 COTAHIST", coverage: "Fechamentos B3", cadence: "Por pregão", detail: "Preço de fechamento oficial para os instrumentos B3 cobertos pelo arquivo." },
  fundos: { source: "official", badge: "Fonte oficial", provider: "CVM Dados Abertos", coverage: "Informes periódicos", cadence: "Por informe", detail: "Dados cadastrais e informes públicos; não são cotações intradiárias." },
  indices: { source: "reference", badge: "Fonte identificada", provider: "B3 / Yahoo Finance", coverage: "Índices de mercado", cadence: "Por pregão ou feed", detail: "Fechamento B3 quando disponível e feeds públicos identificados para referências adicionais." },
  moedas: { source: "official", badge: "Fonte oficial", provider: "Banco Central — PTAX", coverage: "Câmbio de referência", cadence: "Até 5 boletins/dia", detail: "Cotação PTAX oficial de compra e venda, com boletim e data de referência." },
  commodities: { source: "reference", badge: "Feed de mercado", provider: "Yahoo Finance", coverage: "Contratos futuros", cadence: "Conforme o feed", detail: "Referência de mercado por contrato, com possível atraso informado pela fonte." },
  startups: { source: "official", badge: "Base pública", provider: "Receita Federal", coverage: "Dados cadastrais", cadence: "Conforme publicação", detail: "Dados cadastrais empresariais públicos; não há preço, valuation ou rentabilidade pública para exibir." },
};

export function getCategorySource(assetClass: AssetClass) {
  return categorySources[assetClass];
}
