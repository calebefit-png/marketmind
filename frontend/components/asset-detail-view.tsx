"use client";

import Link from "next/link";
import { useMemo } from "react";
import { useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, CalendarDays, Database, LineChart, RefreshCw, ShieldCheck } from "lucide-react";
import { api, type MarketHistoryPoint } from "@/lib/api";
import { PortalShell } from "@/components/portal-shell";
import { Change, MetricCard, PageHeader, SourceBadge } from "@/components/portal-ui";

export function AssetDetailView() {
  const params = useSearchParams();
  const symbol = (params.get("symbol") ?? "").trim().toUpperCase();
  const detail = useQuery({ queryKey: ["verified-asset", symbol], queryFn: () => api.marketAsset(symbol), enabled: Boolean(symbol), refetchInterval: 15 * 60_000, retry: 1 });
  const history = useQuery({ queryKey: ["verified-asset-history", symbol], queryFn: () => api.marketHistory(symbol), enabled: Boolean(symbol), staleTime: 10 * 60_000, retry: 1 });

  if (!symbol) return <PortalShell><EmptyDetail title="Escolha um ativo" description="Abra uma tabela de dados verificados ou informe um símbolo B3 para consultar o histórico disponível." /></PortalShell>;
  if (detail.isLoading) return <PortalShell><EmptyDetail title={`Consultando ${symbol}`} description="Buscando o último fechamento e a proveniência da fonte oficial." /></PortalShell>;
  if (detail.isError || !detail.data) return <PortalShell><EmptyDetail title={`${symbol} ainda não está disponível`} description="O ativo pode não estar na lista gratuita acompanhada ou o histórico ainda não foi sincronizado. Tente novamente após a próxima carga de fechamento B3." /></PortalShell>;

  const { asset, quote } = detail.data;
  const points = history.data?.points ?? [];
  const source = quote.source ?? history.data?.source ?? null;
  const price = quote.value == null ? "—" : quote.value.toLocaleString("pt-BR", { style: "currency", currency: asset.currency || "BRL" });
  const status = quote.data_status === "closing" ? "Fechamento oficial" : quote.data_status === "delayed" ? "Atrasado" : quote.data_status === "real_time" ? "Tempo real" : "Indisponível";
  const asOf = quote.as_of ? new Date(quote.as_of).toLocaleDateString("pt-BR", { timeZone: "UTC" }) : "—";

  return <PortalShell>
    <div className="mb-5"><Link href="/busca" className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 transition hover:text-cyan-200"><ArrowLeft size={14} />Voltar à busca</Link></div>
    <PageHeader eyebrow={`${asset.exchange} · ${asset.asset_class}`} title={asset.symbol} description={asset.name ?? asset.specification ?? "Ativo acompanhado pela base verificável do MarketMind."} actions={<SourceBadge source={quote.data_status === "real_time" ? "real-time" : "official"} label={status} />} />
    <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><MetricCard label="Último fechamento" value={price} detail={quote.as_of ? `Referência ${asOf}` : "Sem referência disponível"} source="official" /><MetricCard label="Variação" value={quote.change_percent == null ? "—" : `${quote.change_percent >= 0 ? "+" : ""}${quote.change_percent.toFixed(2)}%`} delta={quote.change_percent ?? 0} detail="Versus fechamento anterior" source="official" /><MetricCard label="Histórico carregado" value={String(points.length)} detail="Pregões disponíveis" source="official" /><MetricCard label="Estado" value={status} detail={quote.received_at ? `Recebido em ${new Date(quote.received_at).toLocaleDateString("pt-BR")}` : "Aguardando carga"} source="official" /></section>
    <section className="mt-7 grid gap-5 xl:grid-cols-[minmax(0,1.5fr)_minmax(300px,0.7fr)]"><article className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40"><div className="flex items-start justify-between gap-4 border-b border-slate-800 p-5"><div><div className="flex items-center gap-2"><LineChart size={18} className="text-cyan-300" /><h2 className="text-base font-semibold text-slate-100">Histórico de fechamento</h2></div><p className="mt-1 text-xs text-slate-500">Série diária carregada da fonte indicada. Não representa streaming intradiário.</p></div><span className="font-mono text-[11px] text-slate-500">{points.length ? `${points[0].time.slice(0, 10)} → ${points.at(-1)?.time.slice(0, 10)}` : "Sem pontos"}</span></div><div className="p-5"><HistoryChart points={points} /></div></article><article className="rounded-xl border border-slate-800 bg-slate-900/40 p-5"><div className="flex items-center gap-2"><ShieldCheck size={18} className="text-sky-300" /><h2 className="text-base font-semibold text-slate-100">Proveniência</h2></div><dl className="mt-5 space-y-4 text-sm"><DetailRow icon={<Database size={15} />} label="Fonte" value={source?.name ?? "Ainda não disponível"} /><DetailRow icon={<RefreshCw size={15} />} label="Modo" value={source?.update_mode ?? "—"} /><DetailRow icon={<CalendarDays size={15} />} label="Última referência" value={asOf} /></dl>{source?.source_url ? <a href={source.source_url} target="_blank" rel="noreferrer" className="mt-5 block rounded-lg border border-sky-400/20 bg-sky-400/[0.06] px-3 py-2.5 text-center text-xs font-semibold text-sky-200 transition hover:bg-sky-400/[0.1]">Abrir documentação da fonte</a> : null}<p className="mt-4 text-xs leading-relaxed text-slate-500">{source?.license_note ?? "Esta visualização só exibe valores quando existe fonte e estado de atualização identificados."}</p></article></section>
    <section className="mt-7 overflow-hidden rounded-xl border border-slate-800 bg-slate-900/35"><div className="border-b border-slate-800 p-5"><h2 className="text-base font-semibold text-slate-100">Últimos pregões carregados</h2><p className="mt-1 text-xs text-slate-500">OHLC e volume publicados para o ativo, em ordem do mais recente para o mais antigo.</p></div><div className="overflow-x-auto"><table className="w-full min-w-[700px] text-left"><thead className="bg-slate-950/35"><tr>{["Data", "Abertura", "Máxima", "Mínima", "Fechamento", "Volume"].map((header) => <th key={header} className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.12em] text-slate-600 first:text-left">{header}</th>)}</tr></thead><tbody className="divide-y divide-slate-800">{[...points].slice(-30).reverse().map((point) => <HistoryRow key={point.time} point={point} currency={asset.currency} />)}</tbody></table></div>{history.isLoading ? <p className="p-5 text-center text-xs text-slate-500">Carregando série histórica…</p> : null}{!history.isLoading && !points.length ? <p className="p-5 text-center text-xs text-slate-500">A carga histórica ainda não encontrou pregões para este ativo.</p> : null}</section>
  </PortalShell>;
}

function HistoryChart({ points }: { points: MarketHistoryPoint[] }) {
  const chart = useMemo(() => {
    const sample = points.slice(-360);
    if (sample.length < 2) return null;
    const values = sample.map((point) => point.close);
    const min = Math.min(...values); const max = Math.max(...values); const range = max - min || 1;
    return sample.map((point, index) => `${(index / (sample.length - 1)) * 100},${92 - ((point.close - min) / range) * 84}`).join(" ");
  }, [points]);
  if (!chart) return <div className="grid h-[260px] place-items-center rounded-lg border border-dashed border-slate-700 bg-slate-950/25 text-center"><div><p className="text-sm font-medium text-slate-400">Histórico insuficiente</p><p className="mt-1 text-xs text-slate-600">O gráfico aparecerá quando existirem ao menos dois fechamentos verificados.</p></div></div>;
  return <div className="h-[260px] rounded-lg border border-slate-800 bg-slate-950/35 p-3"><svg viewBox="0 0 100 100" preserveAspectRatio="none" className="h-full w-full" aria-label="Gráfico de histórico de fechamento"><defs><linearGradient id="history-fill" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#22d3ee" stopOpacity="0.28" /><stop offset="100%" stopColor="#22d3ee" stopOpacity="0" /></linearGradient></defs><polygon points={`0,100 ${chart} 100,100`} fill="url(#history-fill)" /><polyline points={chart} fill="none" stroke="#67e8f9" strokeWidth="1.2" vectorEffect="non-scaling-stroke" /></svg></div>;
}

function HistoryRow({ point, currency }: { point: MarketHistoryPoint; currency: string }) { const format = (value: number) => value.toLocaleString("pt-BR", { style: "currency", currency: currency || "BRL", maximumFractionDigits: 2 }); return <tr className="hover:bg-slate-800/25"><td className="px-4 py-3 font-mono text-xs text-slate-300">{new Date(point.time).toLocaleDateString("pt-BR", { timeZone: "UTC" })}</td>{[point.open, point.high, point.low, point.close].map((value, index) => <td key={index} className="px-4 py-3 text-right font-mono text-xs text-slate-300">{format(value)}</td>)}<td className="px-4 py-3 text-right font-mono text-xs text-slate-500">{point.volume.toLocaleString("pt-BR", { maximumFractionDigits: 0 })}</td></tr>; }
function DetailRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) { return <div><dt className="flex items-center gap-2 text-xs text-slate-500">{icon}{label}</dt><dd className="mt-1 font-mono text-xs text-slate-200">{value}</dd></div>; }
function EmptyDetail({ title, description }: { title: string; description: string }) { return <div className="grid min-h-[55vh] place-items-center"><div className="max-w-lg rounded-xl border border-dashed border-slate-700 bg-slate-900/25 p-8 text-center"><Database className="mx-auto text-slate-600" size={25} /><h1 className="mt-4 text-xl font-semibold text-slate-100">{title}</h1><p className="mt-2 text-sm leading-relaxed text-slate-500">{description}</p><Link href="/acoes" className="mt-6 inline-flex rounded-lg border border-cyan-400/30 px-3 py-2 text-sm font-semibold text-cyan-200">Ver ações</Link></div></div>; }
