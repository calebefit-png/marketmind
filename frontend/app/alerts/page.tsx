"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import clsx from "clsx";
import { api, type AlertHistoryFilters } from "@/lib/api";

const SELECT_STYLE = "rounded-sm border border-terminal-border bg-terminal-bg px-3 py-2 font-mono text-xs text-terminal-text outline-none focus:border-accent";

export default function AlertsPage() {
  const [filters, setFilters] = useState<AlertHistoryFilters>({ limit: 50 });
  const queryFilters = useMemo(() => filters, [filters]);
  const { data: alerts, isLoading, isError } = useQuery({
    queryKey: ["alert-history", queryFilters],
    queryFn: () => api.recentAlerts(queryFilters),
    refetchInterval: 30_000,
  });
  const { data: preferences } = useQuery({
    queryKey: ["alert-preferences"],
    queryFn: api.alertPreferences,
    refetchInterval: 60_000,
  });

  const update = (field: keyof AlertHistoryFilters, value: string) => {
    setFilters((current) => ({ ...current, [field]: value || undefined }));
  };

  return (
    <div className="min-h-screen bg-terminal-bg">
      <header className="border-b border-terminal-border bg-terminal-panel/60 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-baseline gap-3">
            <h1 className="font-mono text-lg font-bold tracking-tight text-terminal-text">MARKET<span className="text-accent">MIND</span></h1>
            <span className="font-mono text-xs text-terminal-muted">CENTRAL DE ALERTAS</span>
          </div>
          <Link href="/" className="font-mono text-xs text-accent hover:underline">← Voltar ao terminal</Link>
        </div>
      </header>

      <main className="mx-auto max-w-7xl space-y-6 px-6 py-6">
        <section className="rounded-sm border border-terminal-border bg-terminal-panel p-4">
          <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
            <div>
              <h2 className="font-mono text-sm font-semibold uppercase tracking-wide text-terminal-text">Histórico verificável</h2>
              <p className="mt-1 text-xs text-terminal-muted">Eventos persistidos pelo worker; não são recomendações de investimento.</p>
            </div>
            <span className="font-mono text-xs text-terminal-muted">Atualização automática a cada 30 s</span>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-6">
            <input aria-label="Filtrar ativo" placeholder="Ativo, ex.: BTCUSDT" className={SELECT_STYLE} onChange={(event) => update("asset", event.target.value)} />
            <select aria-label="Filtrar severidade" className={SELECT_STYLE} onChange={(event) => update("severity", event.target.value)} defaultValue="">
              <option value="">Severidade: todas</option><option value="INFO">INFO</option><option value="WARNING">WARNING</option><option value="CRITICAL">CRITICAL</option>
            </select>
            <select aria-label="Filtrar canal" className={SELECT_STYLE} onChange={(event) => update("channel", event.target.value)} defaultValue="">
              <option value="">Canal: todos</option><option value="telegram">Telegram</option>
            </select>
            <select aria-label="Filtrar status" className={SELECT_STYLE} onChange={(event) => update("status", event.target.value)} defaultValue="">
              <option value="">Status: todos</option><option value="sent">Enviado</option><option value="pending">Pendente</option><option value="failed">Falhou</option>
            </select>
            <input aria-label="Data inicial" type="date" className={SELECT_STYLE} onChange={(event) => update("dateFrom", event.target.value)} />
            <input aria-label="Data final" type="date" className={SELECT_STYLE} onChange={(event) => update("dateTo", event.target.value)} />
          </div>
        </section>

        <section className="overflow-hidden rounded-sm border border-terminal-border bg-terminal-panel">
          <div className="border-b border-terminal-border px-4 py-3 font-mono text-sm font-semibold uppercase tracking-wide text-terminal-text">Alertas recentes</div>
          {isLoading ? <p className="p-4 text-xs font-mono text-terminal-muted">Carregando histórico…</p> : null}
          {isError ? <p className="p-4 text-xs font-mono text-down">O histórico não está disponível no momento.</p> : null}
          {!isLoading && !isError && !alerts?.length ? <p className="p-4 text-xs font-mono text-terminal-muted">Nenhum alerta corresponde aos filtros atuais.</p> : null}
          {alerts?.length ? <div className="divide-y divide-terminal-border">
            {alerts.map((alert) => <article key={alert.id} className="grid gap-2 px-4 py-4 sm:grid-cols-[auto_1fr_auto] sm:items-start">
              <span className={clsx("w-fit rounded-sm border px-2 py-1 font-mono text-[0.65rem] font-semibold", severityStyle(alert.severity))}>{alert.severity}</span>
              <div>
                <p className="font-mono text-sm text-terminal-text">{alert.asset} · {alert.title}</p>
                <p className="mt-1 text-xs leading-relaxed text-terminal-muted">{alert.message}</p>
                <p className="mt-2 font-mono text-[0.65rem] uppercase tracking-wide text-terminal-muted">{alert.event_type} · {alert.channel} · {alert.status}</p>
              </div>
              <time className="font-mono text-[0.65rem] text-terminal-muted">{formatDate(alert.created_at)}</time>
            </article>)}
          </div> : null}
        </section>

        <section className="rounded-sm border border-terminal-border bg-terminal-panel p-4">
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="font-mono text-sm font-semibold uppercase tracking-wide text-terminal-text">Configuração global</h2>
            <span className="font-mono text-[0.65rem] text-terminal-muted">Alterações são protegidas por ADMIN_NOTIFICATION_SECRET</span>
          </div>
          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <ConfigItem label="Ativos monitorados" value={preferences?.assets.join(", ") || "indisponível"} />
            <ConfigItem label="Canal ativo" value={preferences?.channels.join(", ") || "indisponível"} />
            <ConfigItem label="Severidade mínima" value={preferences?.minimum_severity || "indisponível"} />
            <ConfigItem label="Cooldown" value={preferences ? `${preferences.cooldown_seconds} segundos` : "indisponível"} />
          </div>
          {preferences?.paused ? <p className="mt-4 border-l-2 border-warn pl-3 text-xs text-warn">Os alertas estão globalmente pausados.</p> : null}
        </section>
      </main>
    </div>
  );
}

function ConfigItem({ label, value }: { label: string; value: string }) {
  return <div className="border-l-2 border-terminal-border pl-3"><p className="font-mono text-[0.65rem] uppercase tracking-wide text-terminal-muted">{label}</p><p className="mt-1 font-mono text-sm text-terminal-text">{value}</p></div>;
}

function severityStyle(severity: string) {
  if (severity === "CRITICAL") return "border-down/40 bg-down/10 text-down";
  if (severity === "WARNING") return "border-warn/40 bg-warn/10 text-warn";
  return "border-accent/40 bg-accent/10 text-accent";
}

function formatDate(value: string) {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? "—" : parsed.toLocaleString("pt-BR");
}
