import { BarChart3, Layers3, SlidersHorizontal } from "lucide-react";
import { PortalShell } from "@/components/portal-shell";
import { AssetTable, MetricCard, MiniRanking, PageHeader, SourceBadge, VerifiedAssetTable, VerifiedCategorySummary } from "@/components/portal-ui";
import { getCategorySource } from "@/lib/category-sources";
import { getAssetsByClass, getCategory, type AssetClass } from "@/lib/portal-data";

export function CategoryPage({ categorySlug }: { categorySlug: AssetClass }) {
  const category = getCategory(categorySlug);
  if (!category) return null;
  const assets = getAssetsByClass(category.slug as AssetClass);
  const verifiedClasses: Record<string, string[]> = { acoes: ["stock"], fiis: ["fii"], etfs: ["etf"], bdrs: ["bdr"] };
  const b3Classes = verifiedClasses[category.slug] ?? [];
  const categorySource = getCategorySource(category.slug as AssetClass);

  return <PortalShell>
    <PageHeader eyebrow="Classes de investimento" title={category.label} description={category.description} actions={<div className="flex gap-2"><button className="inline-flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2.5 text-xs font-semibold text-slate-300 transition hover:bg-slate-800"><SlidersHorizontal size={15} />Personalizar tabela</button></div>} />
    {b3Classes.length > 0 ? <VerifiedCategorySummary assetClasses={b3Classes} /> : <section className="mb-7 grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><MetricCard label="Cobertura" value={categorySource.coverage} detail={categorySource.detail} source={categorySource.source} /><MetricCard label="Atualização" value={categorySource.cadence} detail="O horário exibido acompanha a fonte consultada" source={categorySource.source} /><MetricCard label="Fonte" value={categorySource.provider} detail="Origem identificada para esta classe" source={categorySource.source} /><article className="rounded-xl border border-slate-800 bg-slate-900/40 p-4"><div className="flex items-center gap-2"><Layers3 size={16} className="text-cyan-300" /><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">Origem dos dados</p></div><div className="mt-3"><SourceBadge source={categorySource.source} label={categorySource.badge} /></div><p className="mt-2 text-xs text-slate-500">{categorySource.detail}</p></article></section>}
    {b3Classes.length > 0 ? <VerifiedAssetTable title={`${category.label} — dados verificados`} assetClasses={b3Classes} /> : null}
    {assets.length > 0 ? <><AssetTable title={`Todos os ${category.label.toLocaleLowerCase("pt-BR")}`} assets={assets} assetClass={category.slug} description="A tabela exibe somente registros recebidos de fontes verificáveis." /><section className="mt-7 grid gap-5 lg:grid-cols-2"><MiniRanking title={`Destaques em ${category.label}`} assets={assets} metric="change" href="/rankings" /><article className="rounded-xl border border-slate-800 bg-slate-900/40 p-5"><BarChart3 className="text-cyan-300" size={20} /><h2 className="mt-4 text-base font-semibold text-white">Análise com contexto</h2><p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-500">Esta área reunirá métricas específicas para {category.label.toLocaleLowerCase("pt-BR")}, histórico, comparações entre pares e evolução no tempo a partir da origem identificada acima.</p></article></section></> : <section className="rounded-xl border border-dashed border-slate-700 bg-slate-900/25 px-6 py-12 text-center"><BarChart3 className="mx-auto text-slate-600" size={26} /><h2 className="mt-4 text-lg font-semibold text-slate-200">Catálogo sem registros carregados</h2><p className="mx-auto mt-2 max-w-lg text-sm leading-relaxed text-slate-500">A origem desta classe é {categorySource.provider}. A tabela exibirá somente registros recebidos dessa fonte; nenhum dado estimado é mostrado.</p></section>}
  </PortalShell>;
}
