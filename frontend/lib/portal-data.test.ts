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
    expect(assetCategories.every((category) => getAssetsByClass(category.slug).length === 0)).toBe(true);
  });

  it("resolve a categoria e não mantém preços estáticos por classe", () => {
    const fiis = getAssetsByClass("fiis");
    expect(getCategory("fiis")?.label).toBe("FIIs");
    expect(fiis).toEqual([]);
  });

  it("não deixa valores sem fonte verificável no catálogo estático", () => {
    expect(assets).toEqual([]);
  });
});
