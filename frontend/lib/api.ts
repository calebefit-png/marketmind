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

export interface AlertStatus {
  telegram_configured: boolean;
  worker: { status: string; last_run: string | null; last_success: string | null; processed_events: number; sent_alerts: number; last_error: string | null };
  model: { asset: string; available: boolean; reliable: boolean; name: string | null };
  providers: Array<{ name: string; availability: string; detail: string }>;
}

export interface RecentAlert {
  id: string; asset: string; event_type: string; severity: string; title: string; message: string; status: string; channel: string; created_at: string;
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
  btcAnalysis: () => apiFetch<AnalysisResponse>("/analysis/btc"),
  alertStatus: () => apiFetch<AlertStatus>("/alerts/status"),
  recentAlerts: () => apiFetch<RecentAlert[]>("/alerts/recent"),
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
