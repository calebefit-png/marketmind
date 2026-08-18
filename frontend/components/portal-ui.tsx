"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowDownRight, ArrowUpRight, ChevronDown, ChevronUp, Info, Search, SlidersHorizontal } from "lucide-react";
import { formatPrice, getCategory, type AssetClass, type MarketAsset, type SourceKind } from "@/lib/portal-data";
import { api, type VerifiedMarketAsset } from "@/lib/api";
import { normalizeCurrencyCode } from "@/lib/currency";
import { belongsToVerifiedClasses } from "@/lib/verified-market";

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description: string; actions?: React.ReactNode }) {
  return <div className="mb-7 flex flex-col gap-4 border-b border-portal-line pb-6 xl:flex-row xl:items-end xl:justify-between"><div><p className="text-[11px] font-semibold uppercase tracking-[0.2em] text-cyan-300">{eyebrow ?? "MarketMind Intelligence"}</p><h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-white md:text-4xl">{title}</h1><p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-400">{description}</p></div>{actions ? <div className="shrink-0">{actions}</div> : null}</div>;
}

export function SourceBadge({ source, label }: { source: SourceKind; label?: string }) {
  const styles = source === "real-time" ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-300" : source === "official" ? "border-sky-400/20 bg-sky-400/10 text-sky-300" : source === "reference" ? "border-violet-400/20 bg-violet-400/10 text-violet-200" : "border-amber-400/20 bg-amber-400/10 text-amber-200";
  const text = label ?? (source === "real-time" ? "Tempo real" : source === "official" ? "Fonte oficial" : source === "reference" ? "Fonte de referência" : "Indisponível agora");
  return <span className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-wider ${styles}`}><span className="h-1.5 w-1.5 rounded-full bg-current" />{text}</span>;
}

export function MetricCard({ label, value, delta, detail, source = "unavailable", wide = false }: { label: string; value: string; delta?: number | null; detail?: string; source?: SourceKind; wide?: boolean }) {
  const positive = (delta ?? 0) > 0;
  const negative = (delta ?? 0) < 0;
  return <article className={`group rounded-xl border border-slate-800 bg-slate-900/45 p-4 transition hover:-translate-y-0.5 hover:border-slate-700 hover:bg-slate-900/80 ${wide ? "md:col-span-2" : ""}`}><div className="flex items-start justify-between gap-3"><div><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</p><p className="mt-3 font-mono text-xl font-semibold tracking-[-0.05em] text-slate-100 tabular-nums">{value}</p></div><SourceBadge source={source} /></div><div className="mt-3 flex items-center gap-2"><span className={`inline-flex items-center gap-1 font-mono text-xs ${positive ? "text-emerald-400" : negative ? "text-rose-400" : "text-slate-500"}`}>{positive ? <ArrowUpRight size={14} /> : negative ? <ArrowDownRight size={14} /> : null}{delta == null ? "—" : `${delta > 0 ? "+" : ""}${delta.toFixed(2)}%`}</span>{detail ? <span className="truncate text-xs text-slate-500">{detail}</span> : null}</div></article>;
}

export function SectionTitle({ title, subtitle, href, linkLabel = "Ver tudo" }: { title: string; subtitle?: string; href?: string; linkLabel?: string }) {
  return <div className="mb-4 flex items-end justify-between gap-4"><div><h2 className="text-lg font-semibold tracking-[-0.025em] text-white">{title}</h2>{subtitle ? <p className="mt-1 text-xs text-slate-500">{subtitle}</p> : null}</div>{href ? <Link href={href} className="shrink-0 text-xs font-semibold text-cyan-300 transition hover:text-cyan-200">{linkLabel} <span aria-hidden>→</span></Link> : null}</div>;
}

export function AssetTable({ title, assets, assetClass, description, compact = false }: { title?: string; assets: MarketAsset[]; assetClass?: AssetClass; description?: string; compact?: boolean }) {
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState<"ticker" | "change" | "dy" | "pl" | "pvp">("ticker");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const category = assetClass ? getCategory(assetClass) : undefined;
  const filtered = useMemo(() => {
    const normalized = query.toLocaleLowerCase("pt-BR");
    return assets.filter((asset) => `${asset.ticker} ${asset.name} ${asset.sector}`.toLocaleLowerCase("pt-BR").includes(normalized)).sort((left, right) => {
      const leftValue = sortKey === "ticker" ? left.ticker : Number(left[sortKey] ?? -Infinity);
      const rightValue = sortKey === "ticker" ? right.ticker : Number(right[sortKey] ?? -Infinity);
      const direction = sortDirection === "asc" ? 1 : -1;
      return leftValue > rightValue ? direction : leftValue < rightValue ? -direction : 0;
    });
  }, [assets, query, sortDirection, sortKey]);
  const toggleSort = (key: typeof sortKey) => { if (key === sortKey) setSortDirection((direction) => direction === "asc" ? "desc" : "asc"); else { setSortKey(key); setSortDirection("asc"); } };
  const columns = category?.columns ?? ["marketCap", "pl", "pvp", "dy", "roe", "liquidity"];

  return <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/40"><div className="flex flex-col gap-3 border-b border-slate-800 p-4 sm:flex-row sm:items-center sm:justify-between"><div>{title ? <h2 className="text-base font-semibold text-white">{title}</h2> : null}{description ? <p className="mt-1 text-xs text-slate-500">{description}</p> : null}</div><div className="flex items-center gap-2"><div className="relative"><Search className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" size={14} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Filtrar ativos" className="h-9 w-44 rounded-lg border border-slate-700 bg-slate-950 px-3 pl-8 text-xs text-slate-200 outline-none transition placeholder:text-slate-600 focus:border-cyan-400/70" /></div><button className="inline-flex h-9 items-center gap-2 rounded-lg border border-slate-700 px-3 text-xs text-slate-300 transition hover:border-slate-600 hover:bg-slate-800"><SlidersHorizontal size={14} />Filtros</button></div></div>
    <div className="hidden overflow-x-auto md:block"><table className="w-full min-w-[1180px] text-left"><thead className="bg-slate-950/40"><tr><HeaderButton label="Ativo" active={sortKey === "ticker"} direction={sortDirection} onClick={() => toggleSort("ticker")} />{!compact ? <th className="px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.13em] text-slate-600">Setor</th> : null}<th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.13em] text-slate-600">Cotação</th><HeaderButton label="Dia" align="right" active={sortKey === "change"} direction={sortDirection} onClick={() => toggleSort("change")} />{columns.includes("marketCap") ? <th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.13em] text-slate-600">Patrimônio / valor</th> : null}{columns.includes("pl") ? <HeaderButton label="P/L" align="right" active={sortKey === "pl"} direction={sortDirection} onClick={() => toggleSort("pl")} /> : null}{columns.includes("pvp") ? <HeaderButton label="P/VP" align="right" active={sortKey === "pvp"} direction={sortDirection} onClick={() => toggleSort("pvp")} /> : null}{columns.includes("dy") ? <HeaderButton label="DY / taxa" align="right" active={sortKey === "dy"} direction={sortDirection} onClick={() => toggleSort("dy")} /> : null}{columns.includes("roe") ? <th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.13em] text-slate-600">ROE</th> : null}{columns.includes("liquidity") ? <th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.13em] text-slate-600">Liquidez</th> : null}<th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.13em] text-slate-600">Fonte</th></tr></thead><tbody className="divide-y divide-slate-800/80">{filtered.map((asset) => <AssetRow key={`${asset.assetClass}-${asset.ticker}`} asset={asset} showSector={!compact} columns={columns} />)}</tbody></table></div>
    <div className="divide-y divide-slate-800 md:hidden">{filtered.map((asset) => <Link key={`${asset.assetClass}-${asset.ticker}`} href={`/busca?q=${encodeURIComponent(asset.ticker)}`} className="block p-4 transition hover:bg-slate-800/50"><div className="flex items-start justify-between gap-4"><div><p className="font-mono text-sm font-semibold text-cyan-200">{asset.ticker}</p><p className="mt-1 text-sm text-slate-200">{asset.name}</p><p className="mt-1 text-xs text-slate-500">{asset.sector}</p></div><div className="text-right"><p className="font-mono text-sm text-slate-100">{formatPrice(asset.price, asset.assetClass)}</p><Change value={asset.change} /></div></div><div className="mt-3"><SourceBadge source={asset.source} /></div></Link>)}</div>
    {filtered.length === 0 ? <div className="p-8 text-center"><Info className="mx-auto text-slate-600" size={22} /><p className="mt-3 text-sm text-slate-400">Nenhum ativo com fonte verificada está disponível nesta consulta.</p></div> : null}
  </section>;
}

function HeaderButton({ label, active, direction, onClick, align = "left" }: { label: string; active: boolean; direction: "asc" | "desc"; onClick: () => void; align?: "left" | "right" }) {
  return <th className={`px-4 py-3 ${align === "right" ? "text-right" : "text-left"}`}><button onClick={onClick} className={`inline-flex items-center gap-1 text-[10px] font-semibold uppercase tracking-[0.13em] transition ${active ? "text-cyan-300" : "text-slate-600 hover:text-slate-300"}`}>{label}{active ? direction === "asc" ? <ChevronUp size={12} /> : <ChevronDown size={12} /> : null}</button></th>;
}

function AssetRow({ asset, showSector, columns }: { asset: MarketAsset; showSector: boolean; columns: string[] }) {
  return <tr className="group transition hover:bg-slate-800/40"><td className="px-4 py-3.5"><Link href={`/busca?q=${encodeURIComponent(asset.ticker)}`} className="block"><p className="font-mono text-xs font-semibold text-cyan-200">{asset.ticker}</p><p className="mt-0.5 text-xs text-slate-300">{asset.name}</p></Link></td>{showSector ? <td className="px-4 py-3.5 text-xs text-slate-500">{asset.sector}</td> : null}<td className="px-4 py-3.5 text-right font-mono text-xs text-slate-100">{formatPrice(asset.price, asset.assetClass)}</td><td className="px-4 py-3.5 text-right"><Change value={asset.change} /></td>{columns.includes("marketCap") ? <td className="px-4 py-3.5 text-right font-mono text-xs text-slate-300">{asset.marketCap ?? "—"}</td> : null}{columns.includes("pl") ? <td className="px-4 py-3.5 text-right font-mono text-xs text-slate-300">{asset.pl == null ? "—" : asset.pl.toFixed(2)}</td> : null}{columns.includes("pvp") ? <td className="px-4 py-3.5 text-right font-mono text-xs text-slate-300">{asset.pvp == null ? "—" : asset.pvp.toFixed(2)}</td> : null}{columns.includes("dy") ? <td className="px-4 py-3.5 text-right font-mono text-xs text-slate-300">{asset.dy == null ? "—" : `${asset.dy.toFixed(2)}%`}</td> : null}{columns.includes("roe") ? <td className="px-4 py-3.5 text-right font-mono text-xs text-slate-300">{asset.roe == null ? "—" : `${asset.roe.toFixed(2)}%`}</td> : null}{columns.includes("liquidity") ? <td className="px-4 py-3.5 text-right text-xs text-slate-400">{asset.liquidity ?? "—"}</td> : null}<td className="px-4 py-3.5 text-right"><SourceBadge source={asset.source} /></td></tr>;
}

export function Change({ value }: { value: number }) {
  const positive = value > 0;
  const negative = value < 0;
  return <span className={`inline-flex items-center justify-end gap-1 font-mono text-xs ${positive ? "text-emerald-400" : negative ? "text-rose-400" : "text-slate-500"}`}>{positive ? <ArrowUpRight size={13} /> : negative ? <ArrowDownRight size={13} /> : null}{value === 0 ? "—" : `${value > 0 ? "+" : ""}${value.toFixed(2)}%`}</span>;
}

export function VerifiedAssetTable({ title, assetClasses }: { title: string; assetClasses: string[] }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["verified-market-assets", assetClasses.join(",")],
    queryFn: () => api.marketAssets({ limit: 100 }),
    refetchInterval: 60_000,
    retry: 1,
  });
  const items = (data?.items ?? []).filter((asset) => belongsToVerifiedClasses(asset, assetClasses));

  return <section className="mb-7 overflow-hidden rounded-xl border border-sky-400/20 bg-sky-400/[0.035]">
    <div className="flex flex-col gap-3 border-b border-sky-400/15 p-4 sm:flex-row sm:items-start sm:justify-between"><div><div className="flex items-center gap-2"><h2 className="text-base font-semibold text-slate-100">{title}</h2><SourceBadge source="official" label="Fechamento B3" /></div><p className="mt-1 max-w-3xl text-xs leading-relaxed text-slate-500">Arquivo COTAHIST público da B3. São fechamentos históricos oficiais, não cotações em tempo real. A hora e o estado de cada dado aparecem abaixo.</p></div><span className="font-mono text-[11px] text-slate-500">{items.length} ativo(s) carregado(s)</span></div>
    <div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left"><thead className="bg-slate-950/35"><tr><th className="px-4 py-3 text-[10px] font-semibold uppercase tracking-[0.13em] text-slate-600">Ativo</th><th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.13em] text-slate-600">Último fechamento</th><th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.13em] text-slate-600">Variação</th><th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.13em] text-slate-600">Referência</th><th className="px-4 py-3 text-right text-[10px] font-semibold uppercase tracking-[0.13em] text-slate-600">Estado</th></tr></thead><tbody className="divide-y divide-slate-800/80">{items.map((asset) => <VerifiedAssetRow key={`${asset.exchange}-${asset.symbol}`} asset={asset} />)}</tbody></table></div>
    {isLoading ? <VerifiedNotice text="Consultando o catálogo verificado…" /> : null}
    {isError ? <VerifiedNotice text="A fonte verificada está indisponível no momento. Nenhum valor alternativo é exibido." /> : null}
    {!isLoading && !isError && items.length === 0 ? <VerifiedNotice text="A sincronização gratuita ainda não carregou esta classe. Quando houver fechamento B3 validado, ele aparecerá aqui com a fonte e a data de referência." /> : null}
  </section>;
}

export function VerifiedCategorySummary({ assetClasses }: { assetClasses: string[] }) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["verified-category-summary", assetClasses.join(",")],
    queryFn: () => api.marketAssets({ limit: 100 }),
    refetchInterval: 60_000,
    retry: 1,
  });
  const items = (data?.items ?? []).filter((asset) => belongsToVerifiedClasses(asset, assetClasses));
  const quotes = items.filter((asset) => asset.quote?.change_percent != null);
  const positive = quotes.filter((asset) => (asset.quote?.change_percent ?? 0) > 0).length;
  const leader = [...quotes].sort((left, right) => (right.quote?.change_percent ?? -Infinity) - (left.quote?.change_percent ?? -Infinity))[0];
  const latestAsOf = items.map((asset) => asset.quote?.as_of).filter((value): value is string => Boolean(value)).sort().at(-1);
  const latestDate = latestAsOf ? new Date(latestAsOf).toLocaleDateString("pt-BR", { timeZone: "UTC" }) : "Sem fechamento disponível";
  const unavailable = isError ? "Consulta indisponível" : "Aguardando fechamento";

  return <section className="mb-7 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
    <MetricCard label="Ativos exibidos" value={isLoading ? "—" : String(items.length)} detail={isLoading ? "Consultando catálogo" : "Fechamentos verificados"} source="official" />
    <MetricCard label="Altas no painel" value={isLoading ? "—" : `${positive}/${quotes.length}`} detail={isLoading ? "Consultando fonte" : `Referência ${latestDate}`} source="official" />
    <MetricCard label="Maior variação" value={leader?.quote?.change_percent == null ? "—" : `${leader.quote.change_percent > 0 ? "+" : ""}${leader.quote.change_percent.toFixed(2)}%`} detail={leader ? `${leader.symbol} · ${latestDate}` : unavailable} source="official" />
    <article className="rounded-xl border border-slate-800 bg-slate-900/40 p-4"><div className="flex items-center gap-2"><Info size={16} className="text-cyan-300" /><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">Estado da fonte</p></div><div className="mt-3"><SourceBadge source="official" label="Fechamento B3" /></div><p className="mt-2 text-xs text-slate-500">COTAHIST público. Referência: {latestDate}.</p></article>
  </section>;
}

function VerifiedAssetRow({ asset }: { asset: VerifiedMarketAsset }) {
  const quote = asset.quote;
  const value = quote?.value == null ? "—" : quote.value.toLocaleString("pt-BR", { style: "currency", currency: normalizeCurrencyCode(asset.currency), maximumFractionDigits: 2 });
  const asOf = quote?.as_of ? new Date(quote.as_of).toLocaleDateString("pt-BR", { timeZone: "UTC" }) : "—";
  const status = quote?.data_status === "closing" ? "Fechamento" : quote?.data_status === "delayed" ? "Atrasado" : quote?.data_status === "real_time" ? "Tempo real" : "Indisponível";
  return <tr className="transition hover:bg-sky-400/[0.04]"><td className="px-4 py-3.5"><Link href={`/ativo?symbol=${encodeURIComponent(asset.symbol)}`} className="block"><p className="font-mono text-xs font-semibold text-cyan-200">{asset.symbol}</p><p className="mt-0.5 text-xs text-slate-400">{asset.name ?? asset.specification ?? "Ativo B3"}</p></Link></td><td className="px-4 py-3.5 text-right font-mono text-xs text-slate-100">{value}</td><td className="px-4 py-3.5 text-right">{quote?.change_percent == null ? <span className="font-mono text-xs text-slate-600">—</span> : <Change value={quote.change_percent} />}</td><td className="px-4 py-3.5 text-right font-mono text-xs text-slate-400">{asOf}</td><td className="px-4 py-3.5 text-right"><SourceBadge source={quote?.data_status === "real_time" ? "real-time" : "official"} label={status} /></td></tr>;
}

function VerifiedNotice({ text }: { text: string }) {
  return <div className="border-t border-sky-400/15 px-4 py-4 text-center text-xs leading-relaxed text-slate-500">{text}</div>;
}

export function MiniRanking({ title, assets, metric, href }: { title: string; assets: MarketAsset[]; metric: "dy" | "change" | "marketCap"; href: string }) {
  const sorted = [...assets].sort((left, right) => metric === "marketCap" ? (right.marketCap ?? "").localeCompare(left.marketCap ?? "") : Number(right[metric] ?? -Infinity) - Number(left[metric] ?? -Infinity)).slice(0, 5);
  return <article className="rounded-xl border border-slate-800 bg-slate-900/40 p-4"><div className="flex items-center justify-between"><h3 className="text-sm font-semibold text-slate-100">{title}</h3><Link href={href} className="text-xs font-semibold text-cyan-300">Ver ranking</Link></div><div className="mt-4 space-y-1">{sorted.map((asset, index) => <Link key={`${asset.assetClass}-${asset.ticker}`} href={`/busca?q=${encodeURIComponent(asset.ticker)}`} className="flex items-center justify-between rounded-lg px-2 py-2 transition hover:bg-slate-800"><span className="flex min-w-0 items-center gap-3"><span className="font-mono text-[11px] text-slate-600">0{index + 1}</span><span><strong className="font-mono text-xs text-slate-200">{asset.ticker}</strong><span className="ml-2 truncate text-xs text-slate-500">{asset.name}</span></span></span><span className="font-mono text-xs text-slate-200">{metric === "dy" ? asset.dy == null ? "—" : `${asset.dy.toFixed(2)}%` : metric === "change" ? <Change value={asset.change} /> : asset.marketCap ?? "—"}</span></Link>)}</div></article>;
}
