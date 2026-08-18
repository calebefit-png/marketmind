import type { VerifiedMarketAsset } from "@/lib/api";
import type { AssetClass, MarketAsset } from "@/lib/portal-data";
import { verifiedAssetClass } from "./verified-market";

const categoryByVerifiedClass: Record<string, AssetClass> = {
  stock: "acoes",
  fii: "fiis",
  etf: "etfs",
  bdr: "bdrs",
};

function verifiedAssetToCatalogAsset(asset: VerifiedMarketAsset): MarketAsset | null {
  const assetClass = categoryByVerifiedClass[verifiedAssetClass(asset)];
  if (!assetClass) return null;

  return {
    ticker: asset.symbol,
    name: asset.name ?? asset.specification ?? "Ativo B3",
    assetClass,
    sector: asset.specification ?? "Instrumento listado na B3",
    price: asset.quote?.value ?? 0,
    change: asset.quote?.change_percent ?? 0,
    source: "official",
    updatedAt: asset.quote?.as_of ?? "Fechamento B3 sem referência disponível",
  };
}

/** Retorna exclusivamente instrumentos cujas cotações foram obtidas de fonte verificada. */
export function mergeWithVerifiedMarketAssets(
  _baseAssets: MarketAsset[],
  verifiedAssets: VerifiedMarketAsset[],
): MarketAsset[] {
  const converted = verifiedAssets.map(verifiedAssetToCatalogAsset).filter((asset): asset is MarketAsset => asset !== null);
  return converted;
}
