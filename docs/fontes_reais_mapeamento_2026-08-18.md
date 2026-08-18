# Fontes reais mapeadas — 18 de agosto de 2026

## Fontes já utilizáveis

| Domínio | Fonte | Cobertura e estado |
| --- | --- | --- |
| Valores mobiliários B3 | [COTAHIST B3](https://www.b3.com.br/en_us/market-data-and-indices/data-services/market-data/historical-data/equities/historical-quote-data/) | Histórico de preços de valores mobiliários negociados no mercado à vista desde 1986. Fornece abertura, mínima, máxima, média, fechamento, volume e número de negócios. É preço de fechamento histórico; não é cotação intradiária. Os valores não são ajustados por inflação ou eventos corporativos. |
| Câmbio | [PTAX / Banco Central do Brasil](https://opendata.bcb.gov.br/dataset/exchange-rates-daily-bulletins/resource/9880355c-b33e-441a-ab02-ee764075e654) | API pública OData com cotações de compra e venda, boletins diários e endpoints por data/período. A fonte informa até cinco boletins por dia. |
| Criptoativos | [Binance Spot WebSocket Streams](https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams) | Fluxos de negociação e ticker da Binance. A documentação declara atualização em tempo real para fluxos de negócios e livro; estatísticas de janela de 24 horas atualizam em 1 segundo. O portal já utiliza BTC/USDT dessa fonte. |
| Taxa básica | Banco Central do Brasil, série SGS 432 | Série pública da Selic já integrada ao backend; exibir sempre a data de referência devolvida pela fonte. |
| Tesouro Direto | [Histórico de preços e taxas](https://www.tesourodireto.com.br/en/produtos/dados-sobre-titulos/historico-de-precos-e-taxas) | Página oficial com históricos anuais de preços e taxas. A disponibilidade depende do horário de funcionamento e de eventuais manutenções da plataforma; a extração deve tratar indisponibilidade como ausência de dado, nunca como valor estimado. |
| Ibovespa e IFIX | [Yahoo Finance — ^BVSP](https://finance.yahoo.com/quote/%5EBVSP/) e [Yahoo Finance — IFIX.SA](https://finance.yahoo.com/quote/IFIX.SA/) | Feed público integrado ao ticker com valor, fechamento anterior, horário de mercado e origem identificada. A API classifica a resposta como potencialmente atrasada; o portal não a apresenta como fechamento oficial intradiário da B3. |
| Brent | [Yahoo Finance — BZ=F](https://finance.yahoo.com/quote/BZ%3DF/) | Cotação do contrato futuro de Brent integrada ao ticker, com moeda, horário de mercado, variação e aviso de possível atraso do feed público. |
| Tesouro Direto | [Tesouro Transparente — Taxas dos Títulos Ofertados](https://www.tesourotransparente.gov.br/ckan/dataset/taxas-dos-titulos-ofertados-pelo-tesouro-direto/resource/796d2059-14e9-44e3-80c9-2d9e30b405c1) | Arquivo diário oficial de preços e taxas; cada título deve informar a data do arquivo, a taxa e o preço retornados. |
| Fundos de investimento | [CVM — Dados Abertos de Fundos](https://dados.cvm.gov.br/) | Dados cadastrais e informes periódicos públicos; o portal deve identificar o período do informe e nunca apresentá-lo como cotação intradiária. |
| Startups e empresas não listadas | [Receita Federal — Dados Abertos](https://www.gov.br/receitafederal/pt-br/acesso-a-informacao/dados-abertos) | Cadastro empresarial público; útil para situação cadastral e atividade econômica, mas não fornece preço, valuation ou rentabilidade. |

## Decisão de integridade

Nenhum preço, variação, múltiplo, rendimento, patrimônio, índice, câmbio ou commodity será preenchido por valor estático de exemplo. Enquanto uma fonte verificável não estiver integrada para uma categoria, a interface exibirá somente a taxonomia da categoria e um estado explícito de indisponibilidade.

## Limites conhecidos

- COTAHIST resolve fechamentos de instrumentos B3 cobertos pelo arquivo, mas não fornece streaming nem indicadores fundamentalistas completos.
- PTAX é taxa oficial de referência e não substitui necessariamente uma cotação comercial em tempo real de corretora.
- O feed público de Ibovespa, IFIX e Brent pode apresentar atraso e não substitui diretamente a metodologia oficial de fechamento da B3; cada resposta identifica o provedor, horário e status de atraso.

## Endpoint de índices B3 identificado

Uma referência pública de implementação do arquivo oficial da B3 documenta o endpoint `https://sistemaswebb3-listados.b3.com.br/indexStatisticsProxy/IndexCall/GetPortfolioDay`, em JSON, com os parâmetros `index` e `year`. A resposta tem o fechamento por dia (`day`) e mês (`month01` a `month12`), permitindo selecionar o último pregão válido de `IBOV` e `IFIX` e registrar a respectiva data de referência. Fonte de implementação consultada: [rb3 — modelo b3-indexes-historical-data](https://github.com/ropensci/rb3/blob/main/inst/extdata/templates/b3-indexes-historical-data.yaml).
- A cotação cripto é específica do mercado Binance e pode divergir de outra exchange por spread e liquidez.
- Dados de ações internacionais, REITs, commodities e fundamentos exigem fonte verificável com condições de uso compatíveis; não serão preenchidos com valores de referência enquanto essa integração não existir.

## Nota de compilação estática

O frontend usa exportação estática do Next.js. A falha de pré-renderização foi eliminada no script de build ao executar o comando sem herdar `NODE_ENV=development`; a exportação atual foi concluída para as 28 rotas estáticas com Next.js 16.3.1 e Webpack.
