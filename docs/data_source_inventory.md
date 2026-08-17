# Inventário de fontes de dados — MarketMind

## Registro inicial de pesquisa

| Fonte | Classes cobertas | Cobertura declarada | Uso previsto | Situação |
| --- | --- | --- | --- | --- |
| [B3 — Cotações históricas](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/) | Mercado à vista, incluindo ações, fundos e ETFs quando negociados nesse segmento | A B3 informa série de preços desde 1986, com abertura, mínima, máxima, média, fechamento, negócios e volume | Backfill diário de OHLCV e reconciliação de fechamento de ativos brasileiros | Arquivo ZIP de largura fixa; não ajusta inflação nem proventos; não é uma fonte de streaming |
| [CVM — Dados Abertos](https://dados.cvm.gov.br/) | Fundos de investimento, FIIs e informes regulatórios | Conjuntos cadastrais e informes periódicos; o portal identifica informes mensais e trimestrais de FII | Cadastro, patrimônio, dados operacionais, documentos e validação de eventos de fundos | Não substitui preço de negociação em bolsa nem streaming de cotações |
| [CVM — Companhias Abertas](https://dados.cvm.gov.br/dataset/?groups=companhias) | Companhias abertas registradas, DFP, ITR e formulário de referência | Demonstrações anuais e trimestrais publicadas em conjuntos de dados abertos | Normalização de demonstrações financeiras, eventos regulatórios e cálculo rastreável de indicadores | Frequência de divulgação regulatória; não é uma fonte de preço intradiário |
| [BCB — SGS](https://www3.bcb.gov.br/sgspub/) | Séries macroeconômicas, juros, inflação, câmbio e crédito | Séries temporais identificadas por código e disponibilizadas pelo Banco Central | Histórico macro, Selic, câmbio e painel de contexto econômico | Atualização depende da periodicidade oficial de cada série; não é streaming de bolsa |
| [B3 for Developers](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/b3-for-developers/) | APIs e produtos de informação da B3 | A B3 informa que suas APIs são contratadas mediante licença | Caminho de referência para atualização autorizada de mercado B3 em ambiente comercial | Exige contratação e credenciais; não pode ser presumido como fonte pública de streaming |
| [Brapi](https://brapi.dev/docs) | Ações, FIIs, BDRs, ETFs, índices, cripto, câmbio, macro, fundos e Tesouro Direto, conforme sua documentação | REST com endpoints de cotação, histórico, dividendos, financeiros e módulos por classe | Provedor agregado potencial para uma primeira integração brasileira | O teste sem token é limitado a quatro ativos; a página comercial anuncia plano de produção a partir de R$ 99,99/mês no anual; é necessária chave de produção para cobertura ampla |
| [Binance Spot API](https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams) | Pares negociados na Binance | Streams WebSocket para eventos de mercado do ecossistema Binance | Preço e candles ao vivo de pares disponíveis na corretora | Cobertura limitada à Binance; não representa preço agregado de todo o mercado cripto |
| [CoinGecko API](https://docs.coingecko.com/reference/introduction) | Criptoativos e dados agregados de mercado | REST, WebSocket e webhooks; documentação identifica uma Demo API gratuita limitada e uma referência Pro | Catálogo global, métricas agregadas e complemento de histórico | Chave obrigatória; limites e streaming dependem do plano contratado |

> **Princípio de produto:** nenhuma série será apresentada como atualização em tempo real sem que a fonte, o horário e o atraso de mercado sejam identificados na interface. Dados históricos, preços de fechamento e dados de streaming possuem estados distintos.

## Evidência de cobertura histórica

Segundo a página de cotações históricas da B3, a série abrange os preços dos títulos negociados desde 1986 e inclui identificação do ativo, ISIN, tipo de mercado, preços e volume. A documentação também esclarece que os preços **não** são ajustados por inflação ou por proventos, o que exige uma camada própria de eventos corporativos e ajuste de séries antes de apresentar retorno total ou gráfico ajustado. A área internacional de histórico também separa mercado à vista, derivativos e câmbio, sinalizando que classes diferentes devem ter pipelines independentes.

A página internacional da B3 informa ainda que os arquivos do ano corrente possuem séries diárias. A validação do endereço legado de arquivo diário não retornou um artefato público estável; por isso, o modo gratuito não dependerá dele. O backfill seguirá usando arquivos anuais para montar até quinze anos de série e a reconciliação baixará o arquivo anual corrente, que a B3 informa estar atualizado até o último dia útil. Mesmo nesse fluxo, o estado do dado será **fechamento**, e não streaming.

Fontes consultadas: [B3 — Cotações históricas](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/) e [B3 — Historical data](https://www.b3.com.br/en_us/market-data-and-indices/data-services/market-data/historical-data/).

## Evidência de dados regulatórios de fundos

O Portal de Dados Abertos da CVM publica conjuntos para fundos de investimento e documentos específicos de FIIs, incluindo informes mensais e trimestrais. Essa fonte será aplicada à camada de cadastro e fundamentos de fundos, enquanto preços e liquidez continuarão sendo obtidos pelo pipeline de mercado da B3 ou por um provedor licenciado de cotações atualizadas.

Fonte consultada: [Portal Dados Abertos CVM](https://dados.cvm.gov.br/).

## Evidência de fundamentos de companhias abertas

O grupo de dados de companhias da CVM disponibiliza cadastro de emissores, Demonstrações Financeiras Padronizadas (DFP), Informações Trimestrais (ITR) e formulários de referência. A camada de fundamentos do MarketMind deverá preservar a data de competência, a data de entrega, o consolidado/individual e o identificador CVM da companhia. Dessa forma, múltiplos como P/L, P/VP, margem, ROE e dívida líquida serão reprodutíveis a partir de insumos identificados, em vez de números sem origem declarada.

Fonte consultada: [CVM — Conjuntos de Companhias Abertas](https://dados.cvm.gov.br/dataset/?groups=companhias).

## Evidência de séries macroeconômicas

O Sistema Gerenciador de Séries Temporais (SGS) do Banco Central consolida séries econômico-financeiras e disponibiliza interface de consulta por código de série. O MarketMind já usa a série Selic disponível no BCB; a expansão deve adicionar uma tabela de metadados para mapear indicador, código SGS, unidade, periodicidade, regra de revisão e última observação, em vez de fixar valores no frontend.

Fontes consultadas: [BCB — SGS](https://www3.bcb.gov.br/sgspub/) e [Dados Abertos BCB — interface BCData/SGS](https://dadosabertos.bcb.gov.br/).

## Licença para dados atualizados da B3

A página B3 for Developers declara que suas APIs integram sistemas com compartilhamento de dados de mercado para empresas que **contratarem a licença**. Portanto, o histórico público da B3 pode compor a base histórica de longo prazo, mas a plataforma não deve rotular uma atualização de mercado B3 como streaming autorizado sem uma fonte contratada ou outro provedor que possua os direitos de redistribuição adequados.

Fonte consultada: [B3 for Developers](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/b3-for-developers/).

## Provedor agregado com cobertura ampla

A documentação da Brapi enumera endpoints de cotação, histórico, dividendos e demonstrações financeiras para ações, além de módulos dedicados para FIIs, fundos, Tesouro Direto, macroeconomia, moedas e criptoativos. A página também permite testar, sem token, apenas quatro ações indicadas. Sua página de preços declara um plano de produção a partir de R$ 99,99 mensais na modalidade anual. Portanto, a Brapi pode simplificar uma integração de larga cobertura, mas não deve ser configurada como chave gratuita universal ou como fonte de streaming sem que a assinatura, os termos e a latência estejam confirmados.

Fontes consultadas: [Brapi — documentação](https://brapi.dev/docs) e [Brapi — preços](https://brapi.dev/pricing).

## Criptoativos

Para cotações de pares negociados, o MarketMind manterá a integração de WebSocket da Binance com o símbolo, a corretora e o horário de origem aparentes na tela. Para catálogo mais amplo e métricas agregadas, a documentação da CoinGecko prevê endpoints REST, WebSocket e webhooks, mas separa a Demo API gratuita, de escopo e limites reduzidos, das capacidades Pro. Não será usado um preço de Binance para representar, sem indicação, o valor agregado global de um criptoativo.

Fontes consultadas: [Binance Spot WebSocket Streams](https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams) e [CoinGecko API](https://docs.coingecko.com/reference/introduction).
