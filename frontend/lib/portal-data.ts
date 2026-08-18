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

/** @deprecated O estado demo é mantido apenas para compatibilidade de tipos durante a remoção do catálogo legado. */
export type SourceKind = "demo" | "unavailable" | "real-time" | "official";

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

/**
 * Não há catálogo numérico de reserva. As tabelas recebem somente ativos
 * convertidos de fontes verificadas no módulo market-catalog.
 */
export const assets: MarketAsset[] = [];

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
  return value.toLocaleString("pt-BR", { style: "currency", currency, maximumFractionDigits: 2 });
}
