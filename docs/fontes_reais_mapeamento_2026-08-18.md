# Fontes reais mapeadas — 18 de agosto de 2026

## Fontes já utilizáveis

| Domínio | Fonte | Cobertura e estado |
| --- | --- | --- |
| Valores mobiliários B3 | [COTAHIST B3](https://www.b3.com.br/en_us/market-data-and-indices/data-services/market-data/historical-data/equities/historical-quote-data/) | Histórico de preços de valores mobiliários negociados no mercado à vista desde 1986. Fornece abertura, mínima, máxima, média, fechamento, volume e número de negócios. É preço de fechamento histórico; não é cotação intradiária. Os valores não são ajustados por inflação ou eventos corporativos. |
| Câmbio | [PTAX / Banco Central do Brasil](https://opendata.bcb.gov.br/dataset/exchange-rates-daily-bulletins/resource/9880355c-b33e-441a-ab02-ee764075e654) | API pública OData com cotações de compra e venda, boletins diários e endpoints por data/período. A fonte informa até cinco boletins por dia. |
| Criptoativos | [Binance Spot WebSocket Streams](https://developers.binance.com/docs/binance-spot-api-docs/web-socket-streams) | Fluxos de negociação e ticker da Binance. A documentação declara atualização em tempo real para fluxos de negócios e livro; estatísticas de janela de 24 horas atualizam em 1 segundo. O portal já utiliza BTC/USDT dessa fonte. |
| Taxa básica | Banco Central do Brasil, série SGS 432 | Série pública da Selic já integrada ao backend; exibir sempre a data de referência devolvida pela fonte. |
| Tesouro Direto | [Histórico de preços e taxas](https://www.tesourodireto.com.br/en/produtos/dados-sobre-titulos/historico-de-precos-e-taxas) | Página oficial com históricos anuais de preços e taxas. A disponibilidade depende do horário de funcionamento e de eventuais manutenções da plataforma; a extração deve tratar indisponibilidade como ausência de dado, nunca como valor estimado. |

## Decisão de integridade

Nenhum preço, variação, múltiplo, rendimento, patrimônio, índice, câmbio ou commodity será preenchido por valor estático de exemplo. Enquanto uma fonte verificável não estiver integrada para uma categoria, a interface exibirá somente a taxonomia da categoria e um estado explícito de indisponibilidade.

## Limites conhecidos

- COTAHIST resolve fechamentos de instrumentos B3 cobertos pelo arquivo, mas não fornece streaming nem indicadores fundamentalistas completos.
- PTAX é taxa oficial de referência e não substitui necessariamente uma cotação comercial em tempo real de corretora.
- A cotação cripto é específica do mercado Binance e pode divergir de outra exchange por spread e liquidez.
- Dados de ações internacionais, REITs, commodities e fundamentos exigem fonte verificável com condições de uso compatíveis; não serão preenchidos com valores de referência enquanto essa integração não existir.

## Nota de compilação estática

O frontend usa exportação estática do Next.js. Foi reproduzida localmente a falha de pré-renderização `Cannot read properties of null (reading 'useState'/'useContext')`, documentada na issue [Next.js #85668](https://github.com/vercel/next.js/issues/85668). O relato associa o problema a resolução inconsistente de React em instalações de projeto e sugere limpar dependências e reinstalar a partir do lockfile. A instalação local foi limpa e recriada; a falha persistiu também com Webpack e Next.js 16.3.1. A exportação não será publicada até que a geração seja concluída sem esse erro.
