import { describe, expect, it } from "vitest";
import { assetCategories, assets, getAssetsByClass, getCategory } from "./portal-data";

describe("catálogo do portal MarketMind", () => {
  it("mantém uma categoria navegável para cada classe de investimento prevista", () => {
    expect(assetCategories).toHaveLength(15);
    expect(new Set(assetCategories.map((category) => category.slug)).size).toBe(assetCategories.length);
    expect(assetCategories.map((category) => category.slug)).toEqual(expect.arrayContaining([
      "acoes", "fiis", "etfs", "bdrs", "stocks", "reits", "cripto", "renda-fixa",
      "tesouro-direto", "fiagros", "fundos", "indices", "moedas", "commodities", "startups",
    ]));
    expect(assetCategories.every((category) => getAssetsByClass(category.slug).length > 0)).toBe(true);
  });

  it("resolve a categoria e filtra os ativos sem cruzar classes", () => {
    const fiis = getAssetsByClass("fiis");
    expect(getCategory("fiis")?.label).toBe("FIIs");
    expect(fiis.length).toBeGreaterThan(0);
    expect(fiis.every((asset) => asset.assetClass === "fiis")).toBe(true);
  });

  it("expõe a origem dos dados e preserva o par de mercado em tempo real", () => {
    const supportedSources = new Set(["demo", "official", "real-time"]);
    expect(assets.every((asset) => supportedSources.has(asset.source))).toBe(true);
    expect(assets.find((asset) => asset.ticker === "BTC/USDT")).toMatchObject({
      source: "real-time",
      updatedAt: "Tempo real",
    });
  });
});
