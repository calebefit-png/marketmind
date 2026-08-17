# Benchmark de interface — portal financeiro

Data da observação: 17 de agosto de 2026.

## Referência pública analisada

Página: `https://investidor10.com.br/`

Elementos observados na experiência de navegação:

- Cabeçalho com pesquisa global de ativos, acesso direto a mercado, ações, FIIs, ferramentas, notícias, comunidade e carteira.
- Taxa de mercado horizontal com câmbio, índices, criptoativos e ativos de grande interesse.
- Busca proeminente para encontrar ativos, empresas e índices.
- Cobertura por categorias: ações, FIIs, ETFs, stocks internacionais, criptomoedas, fundos de investimento, renda fixa, Tesouro Direto, Fiagros, índices, moedas e startups.
- Ferramentas principais: agenda de dividendos, comparador, rastreadores, rankings e gestão de carteira.
- Blocos densos de rankings e dados financeiros que funcionam como ponto de entrada para descoberta de ativos.

## Auditoria da interface atual do MarketMind

Página: `https://marketmind-l3kg.onrender.com/`

O estado publicado atual é um terminal mínimo de página única. Possui apenas uma barra de marca, cartões de BTC/USDT, Selic e Ibovespa demonstrativo, um gráfico de BTC/USDT e o aviso de não recomendação. Não há descoberta por classes de ativos, pesquisa, navegação de portal, tabelas, rankings, comparadores, rastreadores, carteira, nem acesso visível à central de alertas.

## Direção de produto

O MarketMind deve abandonar a página única em favor de uma arquitetura de portal. A referência será usada para compreender cobertura e padrões de navegação, mas o produto deve ter marca, textos, componentes e linguagem visual próprios.

## Padrões detalhados de listagens

### Ações

- Tabela principal com filtro setorial, opções de ranking, favoritos e personalização de colunas.
- Campos de análise: valor de mercado, P/L, P/VP, dividend yield, margem líquida, patrimônio líquido, lucro, receita, crescimento de receita e lucro, caixa, dívida e taxonomia setorial.
- Atalhos para rankings por valor de mercado, dividend yield, preço pelo método de Graham, margem líquida e histórico de buy and hold.

### FIIs

- Tabela principal com filtros por tipo e segmento, favoritos e personalização de colunas.
- Campos de análise: patrimônio líquido, P/VP, dividend yield, DY médio em cinco anos, liquidez diária, tipo de fundo, variações de preço em múltiplos períodos e segmento.
- Atalhos para rankings por patrimônio, dividend yield, liquidez, menor P/VP e interesse dos usuários.

### Comparação entre ativos

- O fluxo começa em uma seleção pesquisável de ativos, permite comparar até cinco itens e alterna entre ações, FIIs, stocks, BDRs e REITs.
- A comparação organiza indicadores em cartões, tabelas e gráficos, com cortes históricos de 2, 5 e 10 anos.
- Para FIIs, a experiência destaca rentabilidade acumulada, DY atual e histórico, vacância, cotistas e liquidez diária.

### Observação de roteamento

- A rota pública `https://investidor10.com.br/ferramentas/` retornou 404 na observação. As ferramentas devem ser mapeadas pelos seus caminhos específicos, sem assumir que essa rota seja uma fonte canônica.

### Revisão visual da prévia MarketMind

- A nova estrutura de portal mostra navegação superior, faixa de cotações, barra lateral de classes, pesquisa e módulos de dados de forma coerente em desktop.
- A primeira revisão revelou que cinco cartões de mercado ficavam comprimidos no conteúdo principal em 1280 px; o grid foi ajustado para três colunas nesse intervalo e cinco apenas em telas 2XL.
- O gráfico BTC passou a informar explicitamente que aguarda o streaming quando não houver série, evitando uma superfície vazia que poderia ser interpretada como falha de dados.
- A exportação estática gerada pelo Next validou 27 páginas. Na prévia local, o servidor de arquivos usado aplicou fallback para a página inicial em rotas sem extensão; a inspeção de rotas específicas deve usar os arquivos exportados correspondentes ou o servidor FastAPI de produção, que será responsável pelo roteamento final.
- A tentativa de abrir o arquivo exportado de ações pelo proxy também normalizou a URL para a rota sem extensão e retornou ao fallback local. A build confirmou a geração SSG de `/acoes` e das demais categorias; a inspeção visual por rota será retomada no servidor que entrega os arquivos estáticos no Render.
- Após corrigir a prévia para servir diretórios, a página de ações confirmou navegação, dados por classe, filtros e tabela fundamentalista. Em 1280 px, a tabela de dez colunas ficou estreita demais dentro da área ao lado da barra lateral; a tabela passou a ter largura mínima e rolagem horizontal, priorizando números e nomes legíveis.
- A página de comparador foi validada com seleção inicial de PETR4 e VALE3 e apresenta os indicadores de classe, setor, cotação, variação, múltiplos e fonte lado a lado. A ferramenta mostra explicitamente dados demonstrativos quando a conexão de mercado ainda não foi ativada.
- O teste interativo confirmou que a busca do comparador filtra HGLG11 e que a seleção acrescenta o FII à tabela, atualizando o contador de 2/5 para 3/5 e preservando lacunas de múltiplos como `—`, sem inventar valores.
- A matriz de páginas cobre as quinze classes declaradas, incluindo fundos. Cada categoria agora possui ao menos um ativo demonstrativo ou uma fonte identificada para evitar telas de classe vazias durante a exploração.
- Verificação pós-publicação em 17/08/2026: após o push do commit `baf9a9d`, o endpoint público apresentou a tela de despertar do Render Free. Essa tela indica alocação de recursos do serviço adormecido; a interface do portal deve ser verificada após o término da inicialização e da atualização automática.
- A segunda verificação, poucos segundos depois, ainda indicava a etapa de despertar. Não houve resposta de erro da aplicação; é necessário aguardar o término do cold start antes da inspeção visual da versão publicada.
- Verificação pós-correção de publicação em 17/08/2026: a consulta direta ao domínio confirmou a assinatura textual da nova página (`Mercado em contexto, não em ruído`) depois do deploy do commit `7c96e53`. A sessão de navegador ainda mostrou o painel anterior, compatível com cache local de HTML e scripts; a validação visual deve usar uma URL com parâmetro de versão ou recarregamento forçado.
