export type MarketTicker = {
  label: string;
  value: string;
  delta: string;
  direction: "up" | "down" | "neutral";
  source: "official" | "live" | "unavailable";
};

export const marketTickers: MarketTicker[] = [
  { label: "USD", value: "—", delta: "Fonte em integração", direction: "neutral", source: "unavailable" },
  { label: "IBOV", value: "—", delta: "Fonte em integração", direction: "neutral", source: "unavailable" },
  { label: "IFIX", value: "—", delta: "Fonte em integração", direction: "neutral", source: "unavailable" },
  { label: "BTC", value: "ao vivo", delta: "Binance", direction: "neutral", source: "live" },
  { label: "SELIC", value: "oficial", delta: "BCB", direction: "neutral", source: "official" },
  { label: "BRENT", value: "—", delta: "Fonte em integração", direction: "neutral", source: "unavailable" },
];
