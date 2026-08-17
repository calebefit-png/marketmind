export type AssetClass =
  | "acoes"
  | "fiis"
  | "etfs"
  | "bdrs"
  | "stocks"
  | "reits"
  | "cripto"
  | "renda-fixa"
  | "tesouro-direto"
  | "fiagros"
  | "fundos"
  | "indices"
  | "moedas"
  | "commodities"
  | "startups";

export type SourceKind = "demo" | "real-time" | "official";

export interface MarketAsset {
  ticker: string;
  name: string;
  assetClass: AssetClass;
  sector: string;
  price: number;
  change: number;
  marketCap?: string;
  pl?: number | null;
  pvp?: number | null;
  dy?: number | null;
  roe?: number | null;
  liquidity?: string;
  source: SourceKind;
  updatedAt: string;
}

export interface AssetCategory {
  slug: AssetClass;
  label: string;
  singular: string;
  description: string;
  accent: "cyan" | "violet" | "amber" | "emerald" | "rose";
  columns: Array<"marketCap" | "pl" | "pvp" | "dy" | "roe" | "liquidity">;
}

export const assetCategories: AssetCategory[] = [
  { slug: "acoes", label: "Ações", singular: "ação", description: "Empresas listadas na B3, indicadores e rankings fundamentalistas.", accent: "cyan", columns: ["marketCap", "pl", "pvp", "dy", "roe"] },
  { slug: "fiis", label: "FIIs", singular: "fundo imobiliário", description: "Fundos imobiliários, dividendos, patrimônio, liquidez e segmentos.", accent: "violet", columns: ["marketCap", "pvp", "dy", "liquidity"] },
  { slug: "etfs", label: "ETFs", singular: "ETF", description: "Fundos de índice para exposição local, global, temática e alternativa.", accent: "emerald", columns: ["marketCap", "dy", "liquidity"] },
  { slug: "bdrs", label: "BDRs", singular: "BDR", description: "Recibos brasileiros de empresas e ETFs internacionais.", accent: "amber", columns: ["marketCap", "pl", "dy"] },
  { slug: "stocks", label: "Stocks", singular: "stock", description: "Ações internacionais acompanhadas em moeda de referência.", accent: "cyan", columns: ["marketCap", "pl", "dy", "roe"] },
  { slug: "reits", label: "REITs", singular: "REIT", description: "Fundos imobiliários negociados no exterior.", accent: "violet", columns: ["marketCap", "pvp", "dy"] },
  { slug: "cripto", label: "Cripto", singular: "criptoativo", description: "Criptoativos, pares de negociação e sinais técnicos do MarketMind.", accent: "amber", columns: ["marketCap", "liquidity"] },
  { slug: "renda-fixa", label: "Renda fixa", singular: "título de renda fixa", description: "Produtos de crédito, indexadores, emissor e vencimento.", accent: "emerald", columns: ["dy", "liquidity"] },
  { slug: "tesouro-direto", label: "Tesouro Direto", singular: "título público", description: "Títulos públicos, indexadores e horizontes de vencimento.", accent: "emerald", columns: ["dy"] },
  { slug: "fiagros", label: "Fiagros", singular: "Fiagro", description: "Fundos ligados ao agronegócio, crédito e propriedades rurais.", accent: "violet", columns: ["marketCap", "pvp", "dy", "liquidity"] },
  { slug: "fundos", label: "Fundos", singular: "fundo", description: "Fundos de investimento organizados por estratégia e classe.", accent: "violet", columns: ["marketCap", "dy"] },
  { slug: "indices", label: "Índices", singular: "índice", description: "Índices brasileiros e globais para acompanhar o ambiente de mercado.", accent: "cyan", columns: ["liquidity"] },
  { slug: "moedas", label: "Moedas", singular: "moeda", description: "Câmbio, moedas fortes e pares de referência.", accent: "amber", columns: ["liquidity"] },
  { slug: "commodities", label: "Commodities", singular: "commodity", description: "Mercados de energia, metais e agricultura.", accent: "rose", columns: ["liquidity"] },
  { slug: "startups", label: "Startups", singular: "startup", description: "Radar educativo de setores, teses e ecossistema de inovação.", accent: "rose", columns: [] },
];

export const assets: MarketAsset[] = [
  { ticker: "PETR4", name: "Petrobras PN", assetClass: "acoes", sector: "Petróleo, gás e biocombustíveis", price: 42.05, change: 0.65, marketCap: "R$ 548,5 bi", pl: 4.07, pvp: 1.13, dy: 6.99, roe: 24.32, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "VALE3", name: "Vale ON", assetClass: "acoes", sector: "Materiais básicos", price: 71.52, change: -0.25, marketCap: "R$ 316,5 bi", pl: 30.52, pvp: 1.61, dy: 7.87, roe: 4.75, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "ITUB4", name: "Itaú Unibanco PN", assetClass: "acoes", sector: "Financeiro", price: 38.52, change: 0.31, marketCap: "R$ 173,7 bi", pl: 9.18, pvp: 1.97, dy: 9.05, roe: 21.70, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "WEGE3", name: "WEG ON", assetClass: "acoes", sector: "Bens industriais", price: 47.5, change: 0.13, marketCap: "R$ 199,4 bi", pl: 31.88, pvp: 10.57, dy: 4.22, roe: 32.20, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "BBAS3", name: "Banco do Brasil ON", assetClass: "acoes", sector: "Financeiro", price: 18.36, change: 0.33, marketCap: "R$ 105,8 bi", pl: 8.58, pvp: 0.57, dy: 2.97, roe: 18.40, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "TAEE11", name: "Taesa Units", assetClass: "acoes", sector: "Utilidade pública", price: 38.5, change: 0.57, marketCap: "R$ 13,9 bi", pl: 9.44, pvp: 1.48, dy: 8.91, roe: 17.20, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "HGLG11", name: "Pátria Log", assetClass: "fiis", sector: "Logística", price: 164.92, change: 0.42, marketCap: "R$ 7,5 bi", pvp: 0.88, dy: 9.1, liquidity: "R$ 17,3 mi/dia", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "KNCR11", name: "Kinea Rendimentos", assetClass: "fiis", sector: "Recebíveis", price: 103.22, change: 0.06, marketCap: "R$ 10,9 bi", pvp: 1.03, dy: 13.59, liquidity: "R$ 20,6 mi/dia", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "XPML11", name: "XP Malls", assetClass: "fiis", sector: "Shoppings", price: 106.37, change: -0.19, marketCap: "R$ 7,1 bi", pvp: 0.92, dy: 10.9, liquidity: "R$ 14,3 mi/dia", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "BTLG11", name: "BTG Pactual Logística", assetClass: "fiis", sector: "Logística", price: 98.63, change: 0.28, marketCap: "R$ 7,4 bi", pvp: 0.93, dy: 10.38, liquidity: "R$ 9,2 mi/dia", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "KNIP11", name: "Kinea Índice de Preços", assetClass: "fiis", sector: "Recebíveis", price: 96.11, change: -0.14, marketCap: "R$ 7,4 bi", pvp: 0.96, dy: 11.38, liquidity: "R$ 8,1 mi/dia", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "BOVA11", name: "iShares Ibovespa", assetClass: "etfs", sector: "Ações Brasil", price: 143.26, change: 0.14, marketCap: "R$ 14,2 bi", liquidity: "R$ 81,6 mi/dia", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "IVVB11", name: "iShares S&P 500", assetClass: "etfs", sector: "Ações globais", price: 458.1, change: 0.12, marketCap: "R$ 6,9 bi", liquidity: "R$ 28,4 mi/dia", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "SMAL11", name: "iShares Small Cap", assetClass: "etfs", sector: "Small caps", price: 109.1, change: -0.48, marketCap: "R$ 2,2 bi", liquidity: "R$ 8,2 mi/dia", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "HASH11", name: "Hashdex Nasdaq Crypto", assetClass: "etfs", sector: "Cripto", price: 82.65, change: 1.08, marketCap: "R$ 1,3 bi", liquidity: "R$ 5,7 mi/dia", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "AAPL34", name: "Apple BDR", assetClass: "bdrs", sector: "Tecnologia", price: 79.31, change: 0.56, marketCap: "US$ 3,1 tri", pl: 31.2, dy: 0.45, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "AMZO34", name: "Amazon BDR", assetClass: "bdrs", sector: "Consumo e tecnologia", price: 89.55, change: -0.31, marketCap: "US$ 2,1 tri", pl: 35.8, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "TSLA34", name: "Tesla BDR", assetClass: "bdrs", sector: "Automóveis", price: 53.4, change: 1.35, marketCap: "US$ 1,0 tri", pl: 77.1, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "AAPL", name: "Apple", assetClass: "stocks", sector: "Tecnologia", price: 245.27, change: 0.62, marketCap: "US$ 3,1 tri", pl: 31.2, dy: 0.45, roe: 153.0, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "MSFT", name: "Microsoft", assetClass: "stocks", sector: "Tecnologia", price: 418.7, change: 0.36, marketCap: "US$ 3,1 tri", pl: 35.6, dy: 0.71, roe: 34.0, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "AMZN", name: "Amazon", assetClass: "stocks", sector: "Consumo e tecnologia", price: 203.9, change: -0.31, marketCap: "US$ 2,1 tri", pl: 35.8, roe: 23.3, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "O", name: "Realty Income", assetClass: "reits", sector: "Varejo", price: 57.24, change: 0.24, marketCap: "US$ 50,1 bi", pvp: 1.19, dy: 5.58, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "PLD", name: "Prologis", assetClass: "reits", sector: "Logística", price: 111.8, change: -0.12, marketCap: "US$ 103,4 bi", pvp: 1.57, dy: 3.24, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "BTC/USDT", name: "Bitcoin", assetClass: "cripto", sector: "Camada 1", price: 0, change: 0, marketCap: "Atualizado via Binance", liquidity: "Par suportado", source: "real-time", updatedAt: "Tempo real" },
  { ticker: "ETH/USDT", name: "Ethereum", assetClass: "cripto", sector: "Camada 1", price: 3180.42, change: 0.4, marketCap: "US$ 382,4 bi", liquidity: "Dados demonstrativos", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "SOL/USDT", name: "Solana", assetClass: "cripto", sector: "Camada 1", price: 181.84, change: -1.12, marketCap: "US$ 88,5 bi", liquidity: "Dados demonstrativos", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "CDB 110% CDI", name: "CDB pós-fixado", assetClass: "renda-fixa", sector: "Bancário", price: 1000, change: 0, dy: 110, liquidity: "Liquidez no vencimento", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "LCI 94% CDI", name: "LCI pós-fixada", assetClass: "renda-fixa", sector: "Imobiliário", price: 1000, change: 0, dy: 94, liquidity: "Liquidez no vencimento", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "IPCA+ 2035", name: "Tesouro IPCA+", assetClass: "tesouro-direto", sector: "IPCA", price: 1012.3, change: 0, dy: 6.2, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "SELIC 2031", name: "Tesouro Selic", assetClass: "tesouro-direto", sector: "Selic", price: 16825.34, change: 0, dy: 0.12, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "RURA11", name: "Itaú Asset Rural", assetClass: "fiagros", sector: "Crédito rural", price: 8.95, change: 0.19, marketCap: "R$ 1,1 bi", pvp: 0.92, dy: 14.2, liquidity: "R$ 1,6 mi/dia", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "KNCA11", name: "Kinea Crédito Agro", assetClass: "fiagros", sector: "Crédito rural", price: 98.7, change: 0.06, marketCap: "R$ 2,3 bi", pvp: 1.01, dy: 12.4, liquidity: "R$ 2,1 mi/dia", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "FUND-MACRO", name: "Fundo Macro Brasil", assetClass: "fundos", sector: "Multimercado", price: 1425.8, change: 0.21, marketCap: "R$ 2,4 bi", dy: 4.3, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "FUND-AÇÕES", name: "Fundo Estratégia Ações", assetClass: "fundos", sector: "Ações Brasil", price: 1180.45, change: 0.34, marketCap: "R$ 1,1 bi", dy: 2.1, source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "DOLAR", name: "Dólar americano", assetClass: "moedas", sector: "Câmbio", price: 5.22, change: 0.73, liquidity: "Dados demonstrativos", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "EURO", name: "Euro", assetClass: "moedas", sector: "Câmbio", price: 6.05, change: 1.17, liquidity: "Dados demonstrativos", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "OURO", name: "Ouro", assetClass: "commodities", sector: "Metal precioso", price: 23118.33, change: 0.45, liquidity: "Dados demonstrativos", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "BRENT", name: "Petróleo Brent", assetClass: "commodities", sector: "Energia", price: 485.88, change: -0.8, liquidity: "Dados demonstrativos", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "IBOV", name: "Ibovespa", assetClass: "indices", sector: "Ações Brasil", price: 166934.2, change: -0.1, liquidity: "Dados demonstrativos", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "IFIX", name: "Índice de Fundos Imobiliários", assetClass: "indices", sector: "Fundos imobiliários", price: 3686.33, change: -0.17, liquidity: "Dados demonstrativos", source: "demo", updatedAt: "Dados demonstrativos" },
  { ticker: "IA B2B", name: "Radar de inteligência artificial", assetClass: "startups", sector: "Software", price: 0, change: 0, source: "demo", updatedAt: "Conteúdo educativo" },
  { ticker: "CLIMATE", name: "Radar de climate tech", assetClass: "startups", sector: "Tecnologia climática", price: 0, change: 0, source: "demo", updatedAt: "Conteúdo educativo" },
];

export const navigation = [
  { label: "Visão geral", href: "/", items: [] },
  { label: "Mercados", href: "/acoes", items: ["acoes", "fiis", "etfs", "bdrs", "stocks", "reits", "cripto", "renda-fixa", "tesouro-direto", "fiagros", "fundos", "indices", "moedas", "commodities", "startups"] as AssetClass[] },
  { label: "Ferramentas", href: "/rankings", items: [] },
  { label: "Inteligência", href: "/macro", items: [] },
];

export function getCategory(slug: string) {
  return assetCategories.find((category) => category.slug === slug);
}

export function getAssetsByClass(assetClass: AssetClass) {
  return assets.filter((asset) => asset.assetClass === assetClass);
}

export function formatPrice(value: number, assetClass: AssetClass) {
  if (!value) return "—";
  const currency = ["stocks", "reits", "cripto"].includes(assetClass) ? "USD" : "BRL";
  return value.toLocaleString("pt-BR", { style: "currency", currency, maximumFractionDigits: assetClass === "cripto" ? 2 : 2 });
}
