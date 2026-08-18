import { describe, expect, it } from "vitest";
import { normalizeCurrencyCode } from "./currency";

describe("normalizeCurrencyCode", () => {
  it("converte os marcadores históricos da B3 em códigos ISO", () => {
    expect(normalizeCurrencyCode("R$")).toBe("BRL");
    expect(normalizeCurrencyCode("US$")).toBe("USD");
    expect(normalizeCurrencyCode("BRL")).toBe("BRL");
  });

  it("usa BRL como proteção para um código inválido", () => {
    expect(normalizeCurrencyCode("moeda inválida")).toBe("BRL");
    expect(normalizeCurrencyCode(null)).toBe("BRL");
  });
});
