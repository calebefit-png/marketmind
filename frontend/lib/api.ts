/**
 * lib/api.ts
 * Cliente HTTP tipado para a API MarketMind AI (FastAPI backend) e
 * definição do endpoint WebSocket para streaming de preços em tempo real.
 */

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  (typeof window !== "undefined" ? window.location.origin : "http://localhost:8000");

// WS_URL é sempre derivado de API_URL (https->wss, http->ws) para evitar
// desalinhamento em produção quando apenas NEXT_PUBLIC_API_URL é configurado.
// NEXT_PUBLIC_WS_URL, se definido explicitamente, tem prioridade.
export const WS_URL =
  process.env.NEXT_PUBLIC_WS_URL ??
  API_URL.replace("https://", "wss://").replace("http://", "ws://");

export interface PriceTick {
  asset: string;
  price: number;
  timestamp: string;
  source: string;
}

export interface SelicResponse {
  valor_atual: number;
  data: string;
  valor_anterior: number | null;
  variacao: number | null;
}

export type Trend = "ALTA" | "BAIXA" | "LATERAL";

export interface TechnicalIndicators {
  rsi: number | null;
  sma9: number | null;
  sma21: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_hist: number | null;
  bb_upper: number | null;
  bb_lower: number | null;
  bb_middle: number | null;
}

export interface AnalysisResponse {
  asset: string;
  trend: Trend;
  score: number;
  indicators: TechnicalIndicators;
  explanation: string;
}

export interface Candle {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketDataSource {
  id: string;
  name: string;
  source_url: string;
  license_note: string;
  update_mode: string;
  default_delay_seconds: number | null;
}

export interface MarketQuote {
  value: number | null;
  previous_close: number | null;
  change_percent: number | null;
  as_of: string | null;
  received_at: string | null;
  data_status: "real_time" | "closing" | "delayed" | "unavailable" | string;
  source: MarketDataSource | null;
}

export interface VerifiedMarketAsset {
  symbol: string;
  exchange: string;
  asset_class: string;
  name: string | null;
  specification: string | null;
  currency: string;
  active: boolean;
  listed_at: string | null;
  delisted_at: string | null;
  quote: MarketQuote | null;
}

export interface MarketAssetListResponse {
  items: VerifiedMarketAsset[];
  total: number;
  source_note: string;
}

export interface MarketHistoryPoint {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  trades: number | null;
  data_status: string;
  as_of: string;
  received_at: string;
}

export interface MarketAssetDetailResponse {
  asset: VerifiedMarketAsset;
  quote: MarketQuote;
}

export interface MarketHistoryResponse {
  asset: VerifiedMarketAsset;
  timeframe: string;
  points: MarketHistoryPoint[];
  source: MarketDataSource | null;
  truncated: boolean;
  note: string;
}

export interface AlertStatus {
  telegram_configured: boolean;
  worker: { status: string; last_run: string | null; last_success: string | null; processed_events: number; sent_alerts: number; last_error: string | null };
  model: { asset: string; available: boolean; reliable: boolean; name: string | null };
  providers: Array<{ name: string; availability: string; detail: string }>;
}

export interface RecentAlert {
  id: string; asset: string; event_type: string; severity: string; title: string; message: string; status: string; channel: string; created_at: string;
}

export interface AlertHistoryFilters {
  asset?: string;
  severity?: string;
  channel?: string;
  status?: string;
  dateFrom?: string;
  dateTo?: string;
  limit?: number;
}

export interface AlertPreferences {
  scope_key: string;
  assets: string[];
  channels: string[];
  minimum_severity: string;
  cooldown_seconds: number;
  paused: boolean;
  managed_via: string;
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(`API ${path} falhou (${response.status}): ${body}`);
  }

  return response.json() as Promise<T>;
}

export const api = {
  health: () =>
    apiFetch<{
      status: "ok" | "degraded";
      app: string;
      env: string;
      version: string;
      database: "connected" | "not_configured" | "unavailable";
    }>("/health"),
  btcPrice: () => apiFetch<PriceTick>("/market/btc"),
  selic: () => apiFetch<SelicResponse>("/macro/selic"),
  marketAssets: (filters: { query?: string; assetClass?: string; limit?: number } = {}) => {
    const params = new URLSearchParams();
    if (filters.query) params.set("query", filters.query);
    if (filters.assetClass) params.set("asset_class", filters.assetClass);
    params.set("limit", String(filters.limit ?? 50));
    return apiFetch<MarketAssetListResponse>(`/market/assets?${params.toString()}`);
  },
  marketAsset: (symbol: string) => apiFetch<MarketAssetDetailResponse>(`/market/assets/${encodeURIComponent(symbol)}`),
  marketHistory: (symbol: string, limit = 5000) => apiFetch<MarketHistoryResponse>(`/market/assets/${encodeURIComponent(symbol)}/history?limit=${limit}`),
  btcAnalysis: () => apiFetch<AnalysisResponse>("/analysis/btc"),
  alertStatus: () => apiFetch<AlertStatus>("/alerts/status"),
  recentAlerts: (filters: AlertHistoryFilters = {}) => {
    const params = new URLSearchParams();
    if (filters.asset) params.set("asset", filters.asset);
    if (filters.severity) params.set("severity", filters.severity);
    if (filters.channel) params.set("channel", filters.channel);
    if (filters.status) params.set("status", filters.status);
    if (filters.dateFrom) params.set("date_from", new Date(`${filters.dateFrom}T00:00:00`).toISOString());
    if (filters.dateTo) params.set("date_to", new Date(`${filters.dateTo}T23:59:59`).toISOString());
    params.set("limit", String(filters.limit ?? 50));
    return apiFetch<RecentAlert[]>(`/alerts/recent?${params.toString()}`);
  },
  alertPreferences: () => apiFetch<AlertPreferences>("/alerts/preferences"),
};

export function connectMarketSocket(
  onTick: (tick: PriceTick) => void,
  onStatusChange?: (status: "connecting" | "open" | "closed") => void
): () => void {
  let socket: WebSocket | null = null;
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  let closedByClient = false;

  const connect = () => {
    onStatusChange?.("connecting");
    socket = new WebSocket(`${WS_URL}/ws/market`);

    socket.onopen = () => onStatusChange?.("open");

    socket.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        if (parsed?.type === "price_tick") {
          onTick(parsed.data as PriceTick);
        }
      } catch {
        // ignora mensagens malformadas
      }
    };

    socket.onclose = () => {
      onStatusChange?.("closed");
      if (!closedByClient) {
        reconnectTimer = setTimeout(connect, 2000);
      }
    };

    socket.onerror = () => {
      socket?.close();
    };
  };

  connect();

  return () => {
    closedByClient = true;
    if (reconnectTimer) clearTimeout(reconnectTimer);
    socket?.close();
  };
}
