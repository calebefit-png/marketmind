# Cobertura Inicial de Eventos de Alerta

## Escopo verificável na primeira entrega

O processo contínuo de alertas avaliará apenas dados que o backend MarketMind AI já obtém ou persiste de forma verificável. O fluxo Binance atual fornece ticks de `BTCUSDT`, enquanto o histórico de candles permite indicadores técnicos em `1d`. A integração BCB já expõe a série Selic. Assim, a primeira implementação automatizada cobrirá mudança percentual de preço, rompimentos calculados sobre candles, RSI extremo, cruzamento MACD, mudança de tendência, volume e volatilidade anormais quando houver candles suficientes, além de alteração de Selic.

| Grupo | Fonte atual | Estado | Regra inicial possível |
| --- | --- | --- | --- |
| Preço BTC | Stream Binance com fallback REST | Disponível | Variação, rompimento, volatilidade e cooldown por ativo/regra. |
| Indicadores técnicos | Candles diários persistidos | Disponível quando houver histórico suficiente | RSI, MACD, tendência, níveis de suporte/resistência e volume relativo. |
| Macro brasileira | API SGS do Banco Central | Disponível | Mudança na série Selic consultada. |
| Probabilidade de IA | Saída do modelo atual, marcada como não confiável | Não habilitar para alerta decisório | Somente informação técnica se o status do modelo se tornar confiável. |
| B3, FIIs, fluxo institucional, BTG público, whales e notícias | Sem fonte ou adaptador correspondente no backend FastAPI | Pendente de fonte verificável | Receber eventos por adaptador futuro; não gerar alerta sintético. |
| Macro internacional | Sem fonte configurada | Pendente de fonte verificável | Receber eventos por adaptador futuro; não gerar alerta sintético. |

## Critérios de comunicação

O motor classificará alertas em `INFO`, `WARNING` e `CRITICAL`; notificações de oportunidade usarão a expressão **“cenário identificado”** e sempre incluirão hipótese, dados de suporte, horizonte e condição de invalidação. A camada não produzirá frases de compra, venda ou promessa de retorno.

Para reduzir ruído, cada evento passará por deduplicação por ativo, tipo e janela temporal, cooldown persistente e agregação de sinais correlatos. O estado será armazenado no PostgreSQL, permitindo que o processo isolado se recupere de reinicializações sem repetir alertas recentes.

## Contrato do Telegram

A API oficial do Telegram é HTTP e requer HTTPS para chamadas ao endpoint do bot. As respostas expõem o campo booleano `ok` e, em falhas, podem incluir `description`, `error_code` e parâmetros de recuperação. O provedor usará `sendMessage`, `POST`, timeout, retentativas limitadas com backoff e a indicação `retry_after` quando presente. [1]

O limitador local respeitará como limite conservador uma mensagem por segundo por chat, além de limitar o volume global. Essa precaução está alinhada à orientação oficial de que mensagens acima dessa frequência em um único chat podem resultar em erros `429`. [2]

## Referências

[1] [Telegram Bot API — Requests and responses](https://core.telegram.org/bots/api)

[2] [Telegram Bots FAQ — Broadcasting limits](https://core.telegram.org/bots/faq)
