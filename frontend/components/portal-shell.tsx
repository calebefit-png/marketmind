"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import {
  BellRing,
  BookOpen,
  BriefcaseBusiness,
  CandlestickChart,
  ChevronRight,
  CircleDollarSign,
  Compass,
  Gem,
  Landmark,
  LayoutDashboard,
  ListFilter,
  Menu,
  Search,
  Sparkles,
  X,
} from "lucide-react";
import { assetCategories, assets, type AssetClass } from "@/lib/portal-data";

const primaryNav = [
  { label: "Visão geral", href: "/", icon: LayoutDashboard },
  { label: "Mercados", href: "/acoes", icon: CandlestickChart },
  { label: "Ferramentas", href: "/rankings", icon: ListFilter },
  { label: "Inteligência", href: "/macro", icon: Sparkles },
];

const utilityNav = [
  { label: "Carteira", href: "/carteira", icon: BriefcaseBusiness },
  { label: "Dividendos", href: "/dividendos", icon: CircleDollarSign },
  { label: "Alertas", href: "/alerts", icon: BellRing },
  { label: "Guias", href: "/guias", icon: BookOpen },
];

const tickers = [
  { label: "USD", value: "R$ 5,22", delta: "+0,73%", direction: "up" },
  { label: "IBOV", value: "166.934", delta: "−0,10%", direction: "down" },
  { label: "IFIX", value: "3.686", delta: "−0,17%", direction: "down" },
  { label: "BTC", value: "ao vivo", delta: "Binance", direction: "neutral" },
  { label: "SELIC", value: "oficial", delta: "BCB", direction: "neutral" },
  { label: "BRENT", value: "R$ 485,88", delta: "demo", direction: "down" },
];

function isCurrent(pathname: string, href: string) {
  return href === "/" ? pathname === "/" : pathname === href || pathname.startsWith(`${href}/`);
}

export function PortalShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [isMobileNavOpen, setMobileNavOpen] = useState(false);
  const [isMarketOpen, setMarketOpen] = useState(false);

  const results = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("pt-BR");
    if (normalized.length < 2) return [];
    return assets.filter((asset) => `${asset.ticker} ${asset.name}`.toLocaleLowerCase("pt-BR").includes(normalized)).slice(0, 6);
  }, [query]);

  const navigateToAsset = (ticker: string) => {
    setQuery("");
    router.push(`/busca?q=${encodeURIComponent(ticker)}`);
  };

  return (
    <div className="min-h-screen bg-portal-canvas text-portal-ink">
      <header className="sticky top-0 z-40 border-b border-portal-line bg-portal-canvas/95 backdrop-blur-xl">
        <div className="mx-auto flex h-16 max-w-[1600px] items-center gap-3 px-4 lg:px-6">
          <Link href="/" className="group flex shrink-0 items-center gap-2" aria-label="MarketMind — visão geral">
            <span className="grid h-8 w-8 place-items-center rounded-lg bg-cyan-400 text-slate-950 shadow-[0_0_24px_rgba(34,211,238,0.28)]"><Compass size={18} strokeWidth={2.6} /></span>
            <span className="hidden text-base font-bold tracking-[-0.04em] text-white sm:block">MARKET<span className="text-cyan-300">MIND</span></span>
          </Link>

          <nav className="hidden items-center gap-1 lg:flex" aria-label="Navegação principal">
            {primaryNav.map(({ label, href, icon: Icon }) => (
              <Link key={href} href={href} className={`inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition ${isCurrent(pathname, href) ? "bg-slate-800 text-white" : "text-slate-400 hover:bg-slate-900 hover:text-slate-100"}`}>
                <Icon size={15} />{label}
              </Link>
            ))}
            <button onClick={() => setMarketOpen((value) => !value)} aria-expanded={isMarketOpen} className="inline-flex items-center gap-1 rounded-md px-2 py-2 text-sm text-slate-400 transition hover:bg-slate-900 hover:text-slate-100">Classes <ChevronRight className={isMarketOpen ? "rotate-90 transition-transform" : "transition-transform"} size={15} /></button>
          </nav>

          <div className="relative ml-auto w-full max-w-md">
            <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && query.trim()) router.push(`/busca?q=${encodeURIComponent(query.trim())}`); }} placeholder="Busque ativos, empresas, índices" className="h-10 w-full rounded-lg border border-slate-700/80 bg-slate-950/70 pl-9 pr-3 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-cyan-400/70 focus:ring-2 focus:ring-cyan-400/10" />
            {results.length > 0 ? <div className="absolute left-0 right-0 top-12 overflow-hidden rounded-lg border border-slate-700 bg-slate-900 p-1 shadow-2xl">
              {results.map((asset) => <button key={asset.ticker} onClick={() => navigateToAsset(asset.ticker)} className="flex w-full items-center justify-between rounded-md px-3 py-2.5 text-left transition hover:bg-slate-800"><span><strong className="font-mono text-xs text-cyan-300">{asset.ticker}</strong><span className="ml-2 text-sm text-slate-200">{asset.name}</span></span><span className="text-[11px] uppercase tracking-wider text-slate-500">{asset.assetClass}</span></button>)}
            </div> : null}
          </div>

          <div className="hidden shrink-0 items-center gap-2 md:flex">
            <Link href="/alerts" className="grid h-9 w-9 place-items-center rounded-lg border border-slate-700 text-slate-300 transition hover:border-cyan-400/60 hover:text-cyan-200" aria-label="Central de alertas"><BellRing size={17} /></Link>
            <Link href="/carteira" className="rounded-lg bg-cyan-300 px-3 py-2 text-sm font-semibold text-slate-950 transition hover:bg-cyan-200">Minha carteira</Link>
          </div>
          <button className="grid h-9 w-9 shrink-0 place-items-center rounded-lg border border-slate-700 text-slate-300 lg:hidden" onClick={() => setMobileNavOpen(true)} aria-label="Abrir menu"><Menu size={18} /></button>
        </div>
        {isMarketOpen ? <div className="absolute inset-x-0 top-16 hidden border-b border-portal-line bg-slate-950/98 p-6 shadow-2xl lg:block"><div className="mx-auto grid max-w-[1500px] grid-cols-5 gap-x-6 gap-y-1">{assetCategories.map((category) => <Link onClick={() => setMarketOpen(false)} key={category.slug} href={`/${category.slug}`} className="rounded-lg p-3 transition hover:bg-slate-900"><span className="text-sm font-semibold text-slate-100">{category.label}</span><p className="mt-1 text-xs leading-relaxed text-slate-500">{category.description}</p></Link>)}</div></div> : null}
      </header>

      <div className="border-b border-portal-line bg-slate-950/70"><div className="ticker-mask mx-auto flex max-w-[1600px] items-center gap-0 overflow-x-auto px-4 lg:px-6">{tickers.map((ticker) => <div key={ticker.label} className="flex shrink-0 items-center gap-2 border-r border-slate-800 px-4 py-2.5 first:pl-0"><span className="font-mono text-[11px] font-semibold text-slate-500">{ticker.label}</span><span className="font-mono text-xs text-slate-200">{ticker.value}</span><span className={`font-mono text-[11px] ${ticker.direction === "up" ? "text-emerald-400" : ticker.direction === "down" ? "text-rose-400" : "text-slate-500"}`}>{ticker.delta}</span></div>)}</div></div>

      <div className="mx-auto grid max-w-[1600px] grid-cols-1 lg:grid-cols-[232px_minmax(0,1fr)]">
        <aside className="hidden min-h-[calc(100vh-106px)] border-r border-portal-line px-4 py-6 lg:block">
          <p className="mb-3 px-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-600">Explorar</p>
          <nav className="space-y-1" aria-label="Seções do portal">
            {primaryNav.map(({ label, href, icon: Icon }) => <SideLink key={href} href={href} icon={<Icon size={16} />} active={isCurrent(pathname, href)}>{label}</SideLink>)}
          </nav>
          <p className="mb-3 mt-7 px-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-600">Classes de investimento</p>
          <nav className="space-y-0.5">{assetCategories.map((category) => <SideLink key={category.slug} href={`/${category.slug}`} active={isCurrent(pathname, `/${category.slug}`)} icon={<Gem size={15} />}>{category.label}</SideLink>)}</nav>
          <p className="mb-3 mt-7 px-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-600">Acompanhar</p>
          <nav className="space-y-1">{utilityNav.map(({ label, href, icon: Icon }) => <SideLink key={href} href={href} active={isCurrent(pathname, href)} icon={<Icon size={16} />}>{label}</SideLink>)}</nav>
          <div className="mt-8 rounded-xl border border-cyan-400/15 bg-cyan-400/[0.06] p-3"><Landmark size={17} className="text-cyan-300" /><p className="mt-3 text-xs font-semibold text-slate-200">Fontes transparentes</p><p className="mt-1 text-[11px] leading-relaxed text-slate-500">Identificamos dados em tempo real, oficiais e demonstrativos.</p></div>
        </aside>
        <main className="min-w-0 px-4 py-6 lg:px-8 lg:py-8">{children}</main>
      </div>

      {isMobileNavOpen ? <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm lg:hidden"><aside className="h-full w-[min(90vw,360px)] overflow-y-auto border-r border-slate-700 bg-slate-950 p-5 shadow-2xl"><div className="flex items-center justify-between"><span className="font-bold tracking-tight text-white">MARKET<span className="text-cyan-300">MIND</span></span><button onClick={() => setMobileNavOpen(false)} className="grid h-9 w-9 place-items-center rounded-lg border border-slate-700 text-slate-300" aria-label="Fechar menu"><X size={17} /></button></div><p className="mb-3 mt-8 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-600">Navegação</p><nav className="space-y-1">{[...primaryNav, ...utilityNav].map(({ label, href, icon: Icon }) => <Link onClick={() => setMobileNavOpen(false)} key={href} href={href} className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm ${isCurrent(pathname, href) ? "bg-slate-800 text-white" : "text-slate-400"}`}><Icon size={16} />{label}</Link>)}</nav><p className="mb-3 mt-8 text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-600">Classes</p><nav className="grid grid-cols-2 gap-1">{assetCategories.map((category) => <Link onClick={() => setMobileNavOpen(false)} key={category.slug} href={`/${category.slug}`} className="rounded-lg bg-slate-900 px-3 py-2 text-xs text-slate-300">{category.label}</Link>)}</nav></aside></div> : null}
      <footer className="border-t border-portal-line px-4 py-8 lg:px-8"><div className="mx-auto flex max-w-[1600px] flex-col gap-3 text-xs text-slate-500 md:flex-row md:items-center md:justify-between"><span>MarketMind Intelligence · dados e cenários para estudo.</span><span>Não constitui recomendação de investimento.</span></div></footer>
    </div>
  );
}

function SideLink({ href, icon, children, active }: { href: string; icon: React.ReactNode; children: React.ReactNode; active?: boolean }) {
  return <Link href={href} className={`flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-sm transition ${active ? "bg-cyan-400/10 text-cyan-200" : "text-slate-500 hover:bg-slate-900 hover:text-slate-200"}`}>{icon}<span>{children}</span></Link>;
}
