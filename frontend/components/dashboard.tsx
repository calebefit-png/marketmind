"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import { api, connectMarketSocket } from "@/lib/api";
import { useMarketStore } from "@/lib/store";
import { PriceCard } from "@/components/price-card";
import { BtcChart } from "@/components/btc-chart";

// Mock temporário do Ibovespa — item 1 do roadmap substitui por integração real B3.
const IBOV_MOCK = {
  value: 138542.17,
  deltaPct: 0.64,
};

export function Dashboard() {
  const [series, setSeries] = useState<Array<{ time: string; value: number }>>([]);
  const { btcTick, wsStatus, setBtcTick, setWsStatus } = useMarketStore();

  const { data: selic, isLoading: selicLoading } = useQuery({
    queryKey: ["selic"],
    queryFn: api.selic,
    refetchInterval: 60_000,
  });

  const { data: analysis } = useQuery({
    queryKey: ["btc-analysis"],
    queryFn: api.btcAnalysis,
    refetchInterval: 30_000,
    retry: 1,
  });

  const { data: initialPrice } = useQuery({
    queryKey: ["btc-price-initial"],
    queryFn: api.btcPrice,
    staleTime: Infinity,
  });

  const { data: alertStatus } = useQuery({
    queryKey: ["alert-status"],
    queryFn: api.alertStatus,
    refetchInterval: 30_000,
    retry: 1,
  });

  const { data: recentAlerts } = useQuery({
    queryKey: ["recent-alerts"],
    queryFn: api.recentAlerts,
    refetchInterval: 30_000,
    retry: 1,
  });

  useEffect(() => {
    const disconnect = connectMarketSocket(
      (tick) => {
        setBtcTick(tick);
        setSeries((prev) => {
          const next = [...prev, { time: tick.timestamp, value: tick.price }];
          return next.slice(-300);
        });
      },
      (status) => setWsStatus(status)
    );
    return disconnect;
  }, [setBtcTick, setWsStatus]);

  const currentPrice = btcTick?.price ?? initialPrice?.price ?? null;

  const priceFormatted = currentPrice
    ? currentPrice.toLocaleString("en-US", { style: "currency", currency: "USD" })
    : "—";

  const selicFormatted = selic
    ? `${selic.valor_atual.toFixed(6)}%`
    : "—";

  const selicDelta =
    selic?.variacao != null
      ? `${selic.variacao > 0 ? "+" : ""}${selic.variacao.toFixed(6)}%`
      : undefined;

  return (
    <div className="min-h-screen bg-terminal-bg">
      <header className="border-b border-terminal-border bg-terminal-panel/60 backdrop-blur">
        <div className="mx-auto max-w-7xl px-6 py-4 flex items-center justify-between">
          <div className="flex items-baseline gap-3">
            <h1 className="font-mono text-lg font-bold tracking-tight text-terminal-text">
              MARKET<span className="text-accent">MIND</span>
            </h1>
            <span className="text-xs text-terminal-muted font-mono">AI TERMINAL</span>
          </div>
          <div className="flex items-center gap-2 font-mono text-xs">
            <span
              className={clsx(
                "h-1.5 w-1.5 rounded-full",
                wsStatus === "open" && "bg-up",
                wsStatus === "connecting" && "bg-warn animate-pulse",
                wsStatus === "closed" && "bg-down"
              )}
            />
            <span className="text-terminal-muted uppercase">
              {wsStatus === "open" ? "stream conectado" : wsStatus === "connecting" ? "conectando" : "desconectado"}
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-6 py-6 space-y-6">
        <section className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <PriceCard
            label="BTC/USDT"
            value={priceFormatted}
            live={wsStatus === "open"}
            deltaDirection={analysis?.trend === "ALTA" ? "up" : analysis?.trend === "BAIXA" ? "down" : "flat"}
            delta={analysis ? `${analysis.trend} · score ${analysis.score}` : undefined}
          />
          <PriceCard
            label="SELIC"
            value={selicFormatted}
            loading={selicLoading}
            delta={selicDelta}
            deltaDirection={
              selic?.variacao == null ? "flat" : selic.variacao > 0 ? "up" : "down"
            }
            sublabel={selic ? `ref. ${selic.data}` : undefined}
          />
          <PriceCard
            label="IBOVESPA (mock)"
            value={IBOV_MOCK.value.toLocaleString("pt-BR", { minimumFractionDigits: 2 })}
            delta={`${IBOV_MOCK.deltaPct > 0 ? "+" : ""}${IBOV_MOCK.deltaPct.toFixed(2)}%`}
            deltaDirection={IBOV_MOCK.deltaPct > 0 ? "up" : "down"}
            sublabel="integração B3 no roadmap"
          />
        </section>

        <section className="rounded-sm border border-terminal-border bg-terminal-panel p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-mono text-sm font-semibold text-terminal-text uppercase tracking-wide">
              BTC/USDT — tempo real
            </h2>
            {analysis && (
              <span className="text-xs font-mono text-terminal-muted max-w-md text-right">
                {analysis.explanation}
              </span>
            )}
          </div>
          <BtcChart data={series} />
        </section>

        {analysis && (
          <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <IndicatorTile label="RSI (14)" value={analysis.indicators.rsi} />
            <IndicatorTile label="SMA 9" value={analysis.indicators.sma9} currency />
            <IndicatorTile label="SMA 21" value={analysis.indicators.sma21} currency />
            <IndicatorTile label="MACD" value={analysis.indicators.macd} />
          </section>
        )}

        <section className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="rounded-sm border border-terminal-border bg-terminal-panel p-4">
            <h2 className="font-mono text-sm font-semibold text-terminal-text uppercase tracking-wide">Radar operacional</h2>
            <div className="mt-3 space-y-2 text-xs font-mono text-terminal-muted">
              <p>Worker: <span className="text-terminal-text">{alertStatus?.worker.status ?? "indisponível"}</span></p>
              <p>Telegram: <span className="text-terminal-text">{alertStatus?.telegram_configured ? "configurado" : "pendente"}</span></p>
              <p>Modelo BTC: <span className="text-terminal-text">{alertStatus?.model.reliable ? "confiável" : "não confiável / indisponível"}</span></p>
              <p>Eventos: <span className="text-terminal-text">{alertStatus?.worker.processed_events ?? 0}</span> · Alertas enviados: <span className="text-terminal-text">{alertStatus?.worker.sent_alerts ?? 0}</span></p>
            </div>
          </div>
          <div className="lg:col-span-2 rounded-sm border border-terminal-border bg-terminal-panel p-4">
            <h2 className="font-mono text-sm font-semibold text-terminal-text uppercase tracking-wide">Alertas recentes</h2>
            <div className="mt-3 space-y-2">
              {recentAlerts?.length ? recentAlerts.slice(0, 4).map((alert) => (
                <div key={alert.id} className="border-l-2 border-accent pl-3 text-xs">
                  <p className="font-mono text-terminal-text">{alert.asset} · {alert.title}</p>
                  <p className="text-terminal-muted line-clamp-1">{alert.message}</p>
                </div>
              )) : <p className="text-xs font-mono text-terminal-muted">Nenhum alerta persistido ainda.</p>}
            </div>
          </div>
        </section>

        <p className="text-xs text-terminal-muted font-mono text-center pt-4">
          MarketMind AI trabalha com probabilidades e cenários — não constitui recomendação de investimento.
        </p>
      </main>
    </div>
  );
}

function IndicatorTile({
  label,
  value,
  currency,
}: {
  label: string;
  value: number | null | undefined;
  currency?: boolean;
}) {
  return (
    <div className="rounded-sm border border-terminal-border bg-terminal-panel p-3">
      <div className="text-[0.65rem] uppercase tracking-wider text-terminal-muted font-mono">
        {label}
      </div>
      <div className="tabular-tick font-mono text-lg font-semibold mt-1 text-terminal-text">
        {value == null ? "—" : currency ? value.toLocaleString("en-US", { style: "currency", currency: "USD" }) : value.toFixed(2)}
      </div>
    </div>
  );
}
