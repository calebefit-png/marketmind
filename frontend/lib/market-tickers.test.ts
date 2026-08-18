import { describe, expect, it } from "vitest";
import { marketTickers } from "./market-tickers";

describe("marketTickers", () => {
  it("exibe somente fonte identificada ou indisponibilidade explícita", () => {
    expect(marketTickers).toHaveLength(6);
    expect(marketTickers.every((ticker) => ["official", "live", "unavailable"].includes(ticker.source))).toBe(true);
    expect(marketTickers.filter((ticker) => ticker.source === "unavailable").every((ticker) => ticker.value === "—" && ticker.delta === "Fonte em integração")).toBe(true);
  });

  it("não reintroduz os valores estáticos sem fonte verificada", () => {
    const values = marketTickers.flatMap((ticker) => [ticker.value, ticker.delta]);
    expect(values).not.toContain("R$ 5,22");
    expect(values).not.toContain("166.934");
    expect(values).not.toContain("3.686");
    expect(values).not.toContain("R$ 485,88");
    expect(values).not.toContain("demo");
  });
});
