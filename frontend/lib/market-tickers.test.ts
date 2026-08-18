import { describe, expect, it } from "vitest";
import { marketTickers, mergeReferenceTickers } from "./market-tickers";

describe("marketTickers", () => {
  it("consulta fontes identificadas sem exibir valores estáticos", () => {
    expect(marketTickers).toHaveLength(6);
    expect(marketTickers.every((ticker) => ["official", "live", "unavailable"].includes(ticker.source))).toBe(true);
    expect(marketTickers.filter((ticker) => ticker.source === "unavailable").every((ticker) => ticker.value === "—" && ticker.delta === "Consultando fonte")).toBe(true);
  });

  it("não reintroduz os valores estáticos sem fonte verificada", () => {
    const values = marketTickers.flatMap((ticker) => [ticker.value, ticker.delta]);
    expect(values).not.toContain("R$ 5,22");
    expect(values).not.toContain("166.934");
    expect(values).not.toContain("3.686");
    expect(values).not.toContain("R$ 485,88");
    expect(values).not.toContain("demo");
  });

  it("substitui somente os indicadores fornecidos por fontes identificadas", () => {
    const tickers = mergeReferenceTickers({
      items: [
        {
          symbol: "USD/BRL", label: "USD", value: 5.2014, previous_close: null, change_percent: null,
          currency: "BRL", as_of: "2026-08-17T13:04:48", received_at: "2026-08-18T00:00:00Z", data_status: "closing",
          source: { id: "bcb-ptax", name: "BCB PTAX", source_url: "https://example.test", license_note: "oficial", update_mode: "diário", default_delay_seconds: null },
        },
        {
          symbol: "IBOV", label: "IBOV", value: 166783.56, previous_close: 167875, change_percent: -0.65,
          currency: "BRL", as_of: "2026-08-18T00:00:00Z", received_at: "2026-08-18T00:00:00Z", data_status: "delayed",
          source: { id: "yahoo-finance-ibov", name: "Yahoo Finance", source_url: "https://example.test", license_note: "feed", update_mode: "feed", default_delay_seconds: null },
        },
      ],
    });

    expect(tickers.find((ticker) => ticker.label === "USD")).toMatchObject({ value: "R$ 5,2014", delta: "BCB PTAX", source: "official" });
    expect(tickers.find((ticker) => ticker.label === "IBOV")).toMatchObject({ value: "R$ 166.784", direction: "down", source: "live" });
    expect(tickers.find((ticker) => ticker.label === "IFIX")).toMatchObject({ value: "—", source: "unavailable" });
  });
});
