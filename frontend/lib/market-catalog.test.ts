import { describe, expect, it } from "vitest";
import { mergeWithVerifiedMarketAssets } from "./market-catalog";

describe("mergeWithVerifiedMarketAssets", () => {
  it("prioriza o fechamento oficial sem remover ativos ainda cobertos apenas pelo catálogo demonstrativo", () => {
    const merged = mergeWithVerifiedMarketAssets(
      [
        { ticker: "PETR4", name: "Petrobras PN", assetClass: "acoes", sector: "Demo", price: 10, change: 1, source: "demo", updatedAt: "Demo" },
        { ticker: "AAPL", name: "Apple", assetClass: "stocks", sector: "Tecnologia", price: 20, change: 2, source: "demo", updatedAt: "Demo" },
      ],
      [{ symbol: "PETR4", name: "PETROBRAS", specification: "PN", asset_class: "stock", currency: "R$", exchange: "B3", active: true, listed_at: null, delisted_at: null, quote: { value: 42.5, previous_close: 41.8, change_percent: 1.67, as_of: "2026-08-14T00:00:00Z", received_at: "2026-08-17T00:00:00Z", data_status: "closing", source: null } }],
    );

    expect(merged).toHaveLength(2);
    expect(merged.find((asset) => asset.ticker === "PETR4")).toMatchObject({ price: 42.5, change: 1.67, source: "official", assetClass: "acoes" });
    expect(merged.find((asset) => asset.ticker === "AAPL")?.source).toBe("demo");
  });

  it("insere FIIs e ETFs nas classes locais corretas quando a B3 ainda os descreve como fund_or_etf", () => {
    const merged = mergeWithVerifiedMarketAssets([], [
      { symbol: "HGLG11", name: "FII", specification: "CI", asset_class: "fund_or_etf", currency: "R$", exchange: "B3", active: true, listed_at: null, delisted_at: null, quote: null },
      { symbol: "BOVA11", name: "ETF", specification: "CI", asset_class: "fund_or_etf", currency: "R$", exchange: "B3", active: true, listed_at: null, delisted_at: null, quote: null },
    ]);

    expect(merged.find((asset) => asset.ticker === "HGLG11")?.assetClass).toBe("fiis");
    expect(merged.find((asset) => asset.ticker === "BOVA11")?.assetClass).toBe("etfs");
  });
});
