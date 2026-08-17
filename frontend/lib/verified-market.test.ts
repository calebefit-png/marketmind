import { describe, expect, it } from "vitest";
import { belongsToVerifiedClasses, verifiedAssetClass } from "./verified-market";

describe("verifiedAssetClass", () => {
  it("separa fundos imobiliários e ETFs que chegam com classe genérica da B3", () => {
    expect(verifiedAssetClass({ symbol: "HGLG11", asset_class: "fund_or_etf" })).toBe("fii");
    expect(verifiedAssetClass({ symbol: "BOVA11", asset_class: "fund_or_etf" })).toBe("etf");
  });

  it("preserva as classificações já explícitas e não classifica símbolos desconhecidos por suposição", () => {
    expect(verifiedAssetClass({ symbol: "PETR4", asset_class: "stock" })).toBe("stock");
    expect(verifiedAssetClass({ symbol: "DESCONHECIDO11", asset_class: "fund_or_etf" })).toBe("fund_or_etf");
    expect(belongsToVerifiedClasses({ symbol: "IVVB11", asset_class: "fund_or_etf" }, ["etf"])).toBe(true);
    expect(belongsToVerifiedClasses({ symbol: "IVVB11", asset_class: "fund_or_etf" }, ["fii"])).toBe(false);
  });
});
