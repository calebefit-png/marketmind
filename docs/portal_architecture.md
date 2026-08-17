# Arquitetura do Portal MarketMind

## Objetivo de produto

O MarketMind evolui de um terminal de alerta único para um portal brasileiro de inteligência de investimentos. A experiência prioriza descoberta, comparação e leitura de dados, sem apresentar sugestões personalizadas de compra, venda ou alocação. O portal mantém o aviso de que os conteúdos são informativos e não constituem recomendação de investimento.

## Sistema visual

O produto usará uma identidade independente do MarketMind: fundo grafite profundo, superfícies azul-marinho, realce turquesa para ações positivas, coral para quedas e amarelo para sinais de atenção. A navegação será composta por uma barra superior de pesquisa e mercado, uma faixa de cotações e uma barra lateral recolhível para as áreas analíticas. Números financeiros usarão tipografia tabular e monoespaçada; títulos, descrições e controles usarão uma fonte sem serifa de alta legibilidade.

| Elemento | Decisão MarketMind |
| --- | --- |
| Navegação | Barra superior de pesquisa, faixa de mercado e menu lateral por áreas de análise. |
| Dados | Cartões compactos, tabelas ordenáveis, estados de fonte e atualização visíveis. |
| Análise | Gráficos, indicadores e resumos de risco tratados como informação, nunca recomendação. |
| Densidade | Layout desktop-first, com tabelas roláveis e adaptação para cartões no celular. |
| Marca | Logotipo textual MarketMind, terminologia e microcopy próprios; nenhuma marca ou texto da referência. |

## Mapa de navegação

| Área | Rotas planejadas | Capacidades da primeira entrega |
| --- | --- | --- |
| Visão geral | `/` | Painel de mercado, pesquisa, destaques, rankings, sinais, macro e alertas recentes. |
| Ações | `/acoes` | Tabela de múltiplos, ranking, filtros por setor e página de ativo. |
| Fundos imobiliários | `/fiis` | Tabela de DY, P/VP, liquidez, patrimônio, segmento e ranking. |
| ETFs | `/etfs` | Catálogo, exposição, classe, variação e comparação. |
| BDRs e exterior | `/bdrs`, `/stocks`, `/reits` | Listagens, moeda de referência e comparação entre ativos. |
| Criptoativos | `/cripto` | Cotação em tempo real para pares suportados, tendências e métricas técnicas. |
| Renda fixa | `/renda-fixa`, `/tesouro-direto` | Painel de produtos, indexadores, vencimentos e simulador informativo. |
| Outros mercados | `/fiagros`, `/fundos`, `/indices`, `/moedas`, `/commodities`, `/startups` | Catálogos e contexto de mercado por classe. |
| Ferramentas | `/rankings`, `/rastreadores`, `/comparador`, `/dividendos`, `/carteira` | Filtragem, ranking, seleção comparativa, calendário de proventos e acompanhamento de carteira. |
| Inteligência | `/macro`, `/alertas` | Selic, câmbio, commodities, indicadores e central operacional de alertas existente. |
| Conteúdo | `/guias`, `/noticias` | Guias educacionais e espaço de atualização editorial com fonte claramente identificada. |

## Dados e estados de transparência

As cotações e análises de BTC/USDT, a Selic e o histórico de alertas consomem os serviços atuais do MarketMind. Dados B3, FIIs, BDRs, ETFs, fundos, renda fixa, commodities e exterior permanecerão com selo explícito **Dados demonstrativos** até que conectores verificáveis sejam introduzidos. Nenhuma informação demonstrativa será confundida com cotação em tempo real.

| Estado da fonte | Significado visual | Aplicação inicial |
| --- | --- | --- |
| Tempo real | Ponto verde e horário de atualização | BTC/USDT em streaming. |
| Fonte oficial | Selo azul e data de referência | Selic, quando retornada pelo BCB. |
| Dados demonstrativos | Selo âmbar e texto explicativo | Classes de ativos sem fonte integrada. |
| Indisponível | Estado neutro e ação de recarregar | Falhas temporárias de API ou dados. |

## Componentes reutilizáveis

A implementação será organizada com um `PortalShell` compartilhado, `MarketTicker`, `GlobalSearch`, `PageHeader`, `AssetTable`, `RankCard`, `MetricCard`, `SourceBadge`, `FilterBar`, `EmptyState` e `Disclaimer`. As páginas de ativos serão alimentadas por um catálogo de demonstração tipado e por dados reais injetados apenas onde as APIs existentes suportam a atualização.

## Cobertura de ferramentas

O comparador permitirá selecionar até cinco ativos de classes compatíveis e exibirá métrica, período e fonte em colunas. O rastreador aceitará filtros combináveis por classe, setor e indicadores. Rankings terão seleção de métrica e período. A carteira será um ambiente local no navegador, com alocação, custo médio, acompanhamento e aviso de que não há execução de ordens. A agenda de dividendos exibirá somente eventos com fonte disponível; enquanto não houver fonte, a página apresentará um estado claro sem inventar proventos.

## Referência de benchmark

A investigação observou categorias de ações, FIIs, ETFs, stocks internacionais, criptoativos, fundos, renda fixa, Tesouro Direto, Fiagros, índices, moedas e startups; além de rankings, carteira, comparadores e rastreadores. Esses itens orientam a cobertura funcional, não uma cópia literal da interface ou da marca.[1]

## Referências

[1]: https://investidor10.com.br/ "Investidor10 — categorias, rankings e ferramentas observados publicamente"
