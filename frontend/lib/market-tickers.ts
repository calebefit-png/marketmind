import type { ReferenceTickerResponse } from "./api";

export type MarketTicker = {
  label: string;
  value: string;
  delta: string;
  direction: "up" | "down" | "neutral";
  source: "official" | "live" | "unavailable";
};

export const marketTickers: MarketTicker[] = [
  { label: "USD", value: "—", delta: "Consultando fonte", direction: "neutral", source: "unavailable" },
  { label: "IBOV", value: "—", delta: "Consultando fonte", direction: "neutral", source: "unavailable" },
  { label: "IFIX", value: "—", delta: "Consultando fonte", direction: "neutral", source: "unavailable" },
  { label: "BTC", value: "ao vivo", delta: "Binance", direction: "neutral", source: "live" },
  { label: "SELIC", value: "oficial", delta: "BCB", direction: "neutral", source: "official" },
  { label: "BRENT", value: "—", delta: "Consultando fonte", direction: "neutral", source: "unavailable" },
];

function currencyValue(value: number, currency: string | null, label: string): string {
  const digits = label === "USD" ? 4 : label === "IBOV" ? 0 : 2;
  const normalizedCurrency = currency === "USD" || currency === "BRL" ? currency : null;
  if (normalizedCurrency) {
    return new Intl.NumberFormat("pt-BR", {
      style: "currency",
      currency: normalizedCurrency,
      minimumFractionDigits: digits,
      maximumFractionDigits: digits,
    }).format(value);
  }
  return new Intl.NumberFormat("pt-BR", { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value);
}

export function mergeReferenceTickers(response: ReferenceTickerResponse): MarketTicker[] {
  const quotesByLabel = new Map(response.items.map((quote) => [quote.label, quote]));
  return marketTickers.map((ticker) => {
    const quote = quotesByLabel.get(ticker.label);
    if (!quote || quote.value === null || quote.data_status === "unavailable") return ticker;

    const change = quote.change_percent;
    return {
      ...ticker,
      value: currencyValue(quote.value, quote.currency, ticker.label),
      delta: change === null ? quote.source.name : `${change >= 0 ? "+" : ""}${change.toFixed(2)}% · ${quote.source.name}`,
      direction: change === null ? "neutral" : change > 0 ? "up" : change < 0 ? "down" : "neutral",
      source: quote.data_status === "closing" ? "official" : "live",
    };
  });
}
