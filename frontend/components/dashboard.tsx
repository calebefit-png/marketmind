"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowRight, BellRing, ChartNoAxesCombined, Landmark, Radar, ShieldCheck, Sparkles } from "lucide-react";
import { api, connectMarketSocket } from "@/lib/api";
import { useMarketStore } from "@/lib/store";
import { assets } from "@/lib/portal-data";
import { mergeWithVerifiedMarketAssets } from "@/lib/market-catalog";
import { BtcChart } from "@/components/btc-chart";
import { PortalShell } from "@/components/portal-shell";
import { AssetTable, MetricCard, MiniRanking, PageHeader, SectionTitle, SourceBadge } from "@/components/portal-ui";

export function Dashboard() {
  const [series, setSeries] = useState<Array<{ time: string; value: number }>>([]);
  const { btcTick, wsStatus, setBtcTick, setWsStatus } = useMarketStore();
  const { data: selic, isLoading: selicLoading } = useQuery({ queryKey: ["selic"], queryFn: api.selic, refetchInterval: 60_000, retry: 1 });
  const { data: analysis } = useQuery({ queryKey: ["btc-analysis"], queryFn: api.btcAnalysis, refetchInterval: 30_000, retry: 1 });
  const { data: initialPrice } = useQuery({ queryKey: ["btc-price-initial"], queryFn: api.btcPrice, staleTime: Infinity, retry: 1 });
  const { data: verifiedData } = useQuery({ queryKey: ["verified-market-assets"], queryFn: () => api.marketAssets({ limit: 100 }), refetchInterval: 60_000, retry: 1 });
  const { data: alertStatus } = useQuery({ queryKey: ["alert-status"], queryFn: api.alertStatus, refetchInterval: 30_000, retry: 1 });
  const { data: recentAlerts } = useQuery({ queryKey: ["recent-alerts"], queryFn: () => api.recentAlerts({ limit: 4 }), refetchInterval: 30_000, retry: 1 });

  useEffect(() => {
    const disconnect = connectMarketSocket((tick) => {
      setBtcTick(tick);
      setSeries((previous) => [...previous, { time: tick.timestamp, value: tick.price }].slice(-300));
    }, setWsStatus);
    return disconnect;
  }, [setBtcTick, setWsStatus]);

  const currentPrice = btcTick?.price ?? initialPrice?.price ?? null;
  const btcFormatted = currentPrice == null ? "—" : currentPrice.toLocaleString("pt-BR", { style: "currency", currency: "USD", maximumFractionDigits: 2 });
  const selicFormatted = selicLoading ? "Carregando…" : selic ? `${selic.valor_atual.toFixed(2)}%` : "Indisponível";
  const marketAssets = useMemo(() => mergeWithVerifiedMarketAssets(assets, verifiedData?.items ?? []), [verifiedData]);
  const topAssets = marketAssets.slice(0, 8);

  return <PortalShell>
    <PageHeader eyebrow="Terminal de inteligência financeira" title="Mercado em contexto, não em ruído." description="Acompanhe classes de investimento, indicadores, rankings e alertas operacionais em um único terminal. Toda informação demonstra sua fonte e seu estado de atualização." actions={<Link href="/rastreadores" className="inline-flex items-center gap-2 rounded-lg border border-cyan-400/35 bg-cyan-400/10 px-3.5 py-2.5 text-sm font-semibold text-cyan-200 transition hover:bg-cyan-400/15"><Radar size={16} />Abrir rastreador</Link>} />

    <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-5">
      <MetricCard label="BTC/USDT" value={btcFormatted} delta={analysis?.trend === "ALTA" ? 0.01 : analysis?.trend === "BAIXA" ? -0.01 : 0} detail={wsStatus === "open" ? "Streaming conectado" : wsStatus === "connecting" ? "Conectando…" : "Último dado disponível"} source="real-time" />
      <MetricCard label="Selic" value={selicFormatted} delta={selic?.variacao} detail={selic ? `Referência ${selic.data}` : "Série oficial"} source="official" />
      <MetricCard label="Ibovespa" value="—" detail="Fonte de índice em integração" source="unavailable" />
      <MetricCard label="Dólar" value="—" detail="PTAX oficial em integração" source="unavailable" />
      <MetricCard label="IFIX" value="—" detail="Fonte de índice em integração" source="unavailable" />
    </section>

    <section className="mt-7 grid gap-5 xl:grid-cols-[minmax(0,1.45fr)_minmax(320px,0.8fr)]">
      <article className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40"><div className="flex flex-col gap-3 border-b border-slate-800 p-5 sm:flex-row sm:items-start sm:justify-between"><div><div className="flex items-center gap-2"><ChartNoAxesCombined size={17} className="text-cyan-300" /><h2 className="text-base font-semibold text-white">Bitcoin — leitura de mercado</h2></div><p className="mt-1 text-xs leading-relaxed text-slate-500">Série de preço com atualização por streaming e indicadores técnicos operacionais.</p></div><SourceBadge source="real-time" /></div><div className="relative h-[250px] p-4"><BtcChart data={series} height={230} />{series.length === 0 ? <div className="pointer-events-none absolute inset-4 grid place-items-center rounded-lg border border-dashed border-slate-700/70 bg-slate-950/20"><div className="text-center"><p className="text-xs font-medium text-slate-400">Aguardando a primeira atualização do streaming</p><p className="mt-1 text-[11px] text-slate-600">O gráfico será preenchido automaticamente quando a série estiver disponível.</p></div></div> : null}</div><div className="grid border-t border-slate-800 sm:grid-cols-4">{[{ label: "Tendência", value: analysis?.trend ?? "—" }, { label: "Score", value: analysis ? String(analysis.score) : "—" }, { label: "RSI (14)", value: analysis?.indicators.rsi?.toFixed(2) ?? "—" }, { label: "MACD", value: analysis?.indicators.macd?.toFixed(2) ?? "—" }].map((item) => <div key={item.label} className="border-r border-slate-800 px-4 py-3 last:border-r-0"><p className="text-[10px] font-semibold uppercase tracking-wider text-slate-600">{item.label}</p><p className="mt-1 font-mono text-sm text-slate-200">{item.value}</p></div>)}</div>{analysis?.explanation ? <p className="border-t border-slate-800 px-5 py-3 text-xs leading-relaxed text-slate-500">{analysis.explanation}</p> : null}</article>
      <article className="rounded-xl border border-slate-800 bg-slate-900/40 p-5"><div className="flex items-start justify-between"><div><div className="flex items-center gap-2"><BellRing size={17} className="text-amber-300" /><h2 className="text-base font-semibold text-white">Radar operacional</h2></div><p className="mt-1 text-xs text-slate-500">Eventos monitorados pelo MarketMind.</p></div><Link href="/alerts" className="text-xs font-semibold text-cyan-300">Ver central</Link></div><div className="mt-5 space-y-3">{recentAlerts?.length ? recentAlerts.map((alert) => <Link href="/alerts" key={alert.id} className="block rounded-lg border border-slate-800 bg-slate-950/40 p-3 transition hover:border-slate-700"><div className="flex items-center justify-between gap-3"><span className="font-mono text-xs text-cyan-200">{alert.asset}</span><span className={`rounded-full px-2 py-1 text-[10px] font-semibold ${alert.severity === "CRITICAL" ? "bg-rose-400/10 text-rose-300" : alert.severity === "WARNING" ? "bg-amber-400/10 text-amber-200" : "bg-cyan-400/10 text-cyan-200"}`}>{alert.severity}</span></div><p className="mt-2 text-xs text-slate-300">{alert.title}</p></Link>) : <div className="rounded-lg border border-dashed border-slate-700 p-5 text-center"><ShieldCheck className="mx-auto text-slate-600" size={20} /><p className="mt-2 text-xs text-slate-500">Nenhum alerta recente persistido.</p></div>}</div><div className="mt-4 grid grid-cols-2 gap-2 border-t border-slate-800 pt-4"><StatusStat label="Worker" value={alertStatus?.worker.status ?? "indisponível"} /><StatusStat label="Telegram" value={alertStatus?.telegram_configured ? "configurado" : "pendente"} /></div></article>
    </section>

    <section className="mt-8"><SectionTitle title="Ativos em evidência" subtitle="Fechamentos B3 verificados disponíveis no terminal." href="/rankings" linkLabel="Explorar rankings" /><AssetTable assets={topAssets} description="Exibe somente ativos cujo fechamento foi carregado pela fonte oficial B3." compact /></section>

    <section className="mt-8 grid gap-5 xl:grid-cols-3"><MiniRanking title="Maiores dividendos" assets={marketAssets.filter((asset) => asset.dy != null)} metric="dy" href="/rankings" /><MiniRanking title="Movimentação do dia" assets={marketAssets.filter((asset) => asset.change !== 0)} metric="change" href="/rankings" /><article className="rounded-xl border border-cyan-400/15 bg-gradient-to-br from-cyan-400/[0.11] to-slate-900/35 p-5"><Sparkles className="text-cyan-300" size={20} /><h2 className="mt-5 text-lg font-semibold tracking-[-0.025em] text-white">Análise antes da decisão.</h2><p className="mt-2 text-sm leading-relaxed text-slate-400">Compare dados verificados, rastreie filtros, acompanhe sua carteira e identifique a origem de cada número exibido.</p><div className="mt-5 grid gap-2"><Link href="/comparador" className="flex items-center justify-between rounded-lg bg-slate-950/55 px-3 py-2.5 text-sm font-medium text-slate-200 transition hover:bg-slate-950">Comparar ativos <ArrowRight size={15} /></Link><Link href="/carteira" className="flex items-center justify-between rounded-lg bg-slate-950/55 px-3 py-2.5 text-sm font-medium text-slate-200 transition hover:bg-slate-950">Acompanhar carteira <ArrowRight size={15} /></Link></div></article></section>

    <section className="mt-8 rounded-xl border border-slate-800 bg-slate-900/35 p-5"><div className="flex items-start gap-3"><Landmark className="mt-0.5 text-sky-300" size={18} /><div><h2 className="text-sm font-semibold text-slate-100">Transparência de dados</h2><p className="mt-1 max-w-4xl text-xs leading-relaxed text-slate-500">BTC/USDT utiliza streaming de mercado, a Selic usa a série pública do Banco Central e os instrumentos B3 exibidos usam fechamento oficial carregado pelo COTAHIST. Classes sem fonte integrada mostram indisponibilidade, não valores de exemplo.</p></div></div></section>
  </PortalShell>;
}

function StatusStat({ label, value }: { label: string; value: string }) {
  return <div className="rounded-lg bg-slate-950/50 p-3"><p className="text-[10px] font-semibold uppercase tracking-wider text-slate-600">{label}</p><p className="mt-1 truncate font-mono text-xs text-slate-300">{value}</p></div>;
}
