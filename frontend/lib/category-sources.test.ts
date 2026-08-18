import { describe, expect, it } from "vitest";
import { categorySources } from "./category-sources";
import { assetCategories } from "./portal-data";

describe("categorySources", () => {
  it("associa todas as classes públicas a uma origem identificada", () => {
    expect(Object.keys(categorySources).sort()).toEqual(assetCategories.map((category) => category.slug).sort());
    expect(Object.values(categorySources).every((source) => source.provider.length > 0 && source.detail.length > 0)).toBe(true);
  });

  it("não usa rótulo genérico de fonte pendente", () => {
    expect(JSON.stringify(categorySources)).not.toMatch(/não integrada|aguardando conector|demonstrativ/i);
  });
});
