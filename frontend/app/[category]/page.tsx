import { notFound } from "next/navigation";
import { BarChart3, Layers3, SlidersHorizontal } from "lucide-react";
import { PortalShell } from "@/components/portal-shell";
import { AssetTable, MetricCard, MiniRanking, PageHeader, SourceBadge } from "@/components/portal-ui";
import { assetCategories, getAssetsByClass, getCategory, type AssetClass } from "@/lib/portal-data";

export function generateStaticParams() {
  return assetCategories.map((category) => ({ category: category.slug }));
}

export default async function CategoryPage({ params }: { params: Promise<{ category: string }> }) {
  const { category: categorySlug } = await params;
  const category = getCategory(categorySlug);
  if (!category) notFound();
  const assets = getAssetsByClass(category.slug as AssetClass);
  const positive = assets.filter((asset) => asset.change > 0).length;
  const topYield = [...assets].sort((left, right) => (right.dy ?? -Infinity) - (left.dy ?? -Infinity))[0];

  return <PortalShell>
    <PageHeader eyebrow="Classes de investimento" title={category.label} description={category.description} actions={<div className="flex gap-2"><button className="inline-flex items-center gap-2 rounded-lg border border-slate-700 px-3 py-2.5 text-xs font-semibold text-slate-300 transition hover:bg-slate-800"><SlidersHorizontal size={15} />Personalizar tabela</button></div>} />
    <section className="mb-7 grid gap-3 sm:grid-cols-2 xl:grid-cols-4"><MetricCard label="Ativos exibidos" value={String(assets.length)} detail="Catálogo inicial" source="demo" /><MetricCard label="Altas no painel" value={`${positive}/${assets.length || 0}`} detail="Variação demonstrativa" source="demo" /><MetricCard label={topYield ? "Maior DY / taxa" : "Fonte"} value={topYield?.dy == null ? "Aguardando conector" : `${topYield.dy.toFixed(2)}%`} detail={topYield?.ticker ?? "Sem dados financeiros"} source="demo" /><article className="rounded-xl border border-slate-800 bg-slate-900/40 p-4"><div className="flex items-center gap-2"><Layers3 size={16} className="text-cyan-300" /><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">Estado da fonte</p></div><div className="mt-3"><SourceBadge source="demo" /></div><p className="mt-2 text-xs text-slate-500">A integração oficial desta classe será identificada nesta área.</p></article></section>
    {assets.length > 0 ? <><AssetTable title={`Todos os ${category.label.toLocaleLowerCase("pt-BR")}`} assets={assets} assetClass={category.slug} description="Use a busca e a ordenação para explorar o catálogo. Todos os números nesta tela exibem o estado de fonte." /><section className="mt-7 grid gap-5 lg:grid-cols-2"><MiniRanking title={`Destaques em ${category.label}`} assets={assets} metric="change" href="/rankings" /><article className="rounded-xl border border-slate-800 bg-slate-900/40 p-5"><BarChart3 className="text-cyan-300" size={20} /><h2 className="mt-4 text-base font-semibold text-white">Análise com contexto</h2><p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-500">Em breve, esta área reunirá métricas específicas para {category.label.toLocaleLowerCase("pt-BR")}, histórico, comparações entre pares e evolução no tempo. Até a conexão de uma fonte verificável, os dados do catálogo são demonstrativos.</p></article></section></> : <section className="rounded-xl border border-dashed border-slate-700 bg-slate-900/25 px-6 py-12 text-center"><BarChart3 className="mx-auto text-slate-600" size={26} /><h2 className="mt-4 text-lg font-semibold text-slate-200">Painel em preparação</h2><p className="mx-auto mt-2 max-w-lg text-sm leading-relaxed text-slate-500">A estrutura de análise para {category.label.toLocaleLowerCase("pt-BR")} já está disponível no portal. O catálogo desta classe será exibido quando houver uma fonte de dados identificada.</p></section>}
  </PortalShell>;
}
