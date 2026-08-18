const currencyAliases: Record<string, string> = {
  "R$": "BRL",
  "US$": "USD",
};

export function normalizeCurrencyCode(currency: string | null | undefined, fallback = "BRL") {
  const normalized = (currency ?? "").trim().toUpperCase();
  const resolved = currencyAliases[normalized] ?? normalized;
  return /^[A-Z]{3}$/.test(resolved) ? resolved : fallback;
}
