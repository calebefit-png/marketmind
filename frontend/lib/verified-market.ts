import type { VerifiedMarketAsset } from "@/lib/api";

/**
 * Alguns instrumentos de cota B3 chegam no COTAHIST com a especificação
 * genérica "CI". Enquanto a próxima sincronização atualiza o catálogo do
 * backend, esta classificação explícita mantém FII e ETF nas páginas certas.
 */
const B3_FII_SYMBOLS = new Set(["BCFF11", "HGLG11", "KNRI11", "MXRF11", "XPLG11"]);
const B3_ETF_SYMBOLS = new Set(["BOVA11", "IVVB11", "SMAL11"]);

export function verifiedAssetClass(asset: Pick<VerifiedMarketAsset, "symbol" | "asset_class">): string {
  if (asset.asset_class !== "fund_or_etf") return asset.asset_class;
  if (B3_FII_SYMBOLS.has(asset.symbol)) return "fii";
  if (B3_ETF_SYMBOLS.has(asset.symbol)) return "etf";
  return asset.asset_class;
}

export function belongsToVerifiedClasses(asset: Pick<VerifiedMarketAsset, "symbol" | "asset_class">, assetClasses: string[]): boolean {
  return assetClasses.includes(verifiedAssetClass(asset));
}
