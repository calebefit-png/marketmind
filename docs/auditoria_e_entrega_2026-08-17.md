# MarketMind AI — Auditoria e Entrega Técnica

**Data:** 17 de agosto de 2026

**Escopo:** dados verificáveis gratuitos, estabilidade, segurança e validação do portal.
**Preservação visual:** o layout, a navegação, a tipografia, a paleta e a composição previamente aprovados foram preservados. Esta entrega não contém reformulação de interface.

## Resumo executivo

O MarketMind está estruturado como um portal de inteligência financeira com fontes e estados de dado explícitos. O catálogo B3 usa o arquivo público COTAHIST como referência de **fechamento oficial**, sem apresentá-lo como cotação intradiária. A Selic vem da série pública do Banco Central e o BTC/USDT possui atualização por Binance, com fallback REST quando necessário. [1] [2] [3]

Na auditoria desta entrega, todas as rotas principais do portal responderam com sucesso após o redirecionamento normal de barra final da exportação estática, os endpoints de mercado responderam corretamente, a validação de limites retornou `422` como esperado, a suíte backend passou com 38 testes, e o frontend passou em testes, tipagem e build de produção.

| Indicador auditado | Resultado | Observação |
|---|---:|---|
| Rotas de interface verificadas em produção | 26 | Todas finalizaram em `200` após redirecionamento estático normal (`307` → `200`). |
| Endpoints de mercado verificados | 5 | Catálogo, detalhe, histórico, Selic e BTC responderam `200`. |
| Ativos B3 verificados disponíveis no catálogo no momento da checagem | 18 | Com proveniência B3 COTAHIST e estado de fechamento. |
| Testes unitários do backend | 38 aprovados | Executados sem injetar URL de banco externa no ambiente de teste. |
| Testes do frontend | 7 aprovados | Inclui classificação e mesclagem do catálogo verificado. |
| Build estática do frontend | Aprovada | 28 páginas geradas com sucesso via Webpack. |

## Recursos adicionados

### Portal e navegação financeira

Foi implementado o portal financeiro com barra lateral, busca, tabelas, cards e páginas para ações, FIIs, ETFs, BDRs, stocks, REITs, cripto, renda fixa, Tesouro Direto, Fiagros, fundos, índices, moedas, commodities e startups. Também foram disponibilizadas páginas de rankings, rastreador, comparador, carteira, dividendos, macro, guias, busca, página de detalhe do ativo e central de alertas.

As ferramentas continuam distinguindo dados verificáveis de informações demonstrativas. Onde não existe fonte pública validada e licenciada para o caso de uso, não há substituição silenciosa de conteúdo por números fabricados.

### Base de dados e proveniência

O backend recebeu um catálogo canônico de ativos, séries de candles, fontes, execuções de ingestão e campos de proveniência. Os endpoints públicos são:

| Endpoint | Finalidade | Estado de dado |
|---|---|---|
| `GET /market/assets` | Lista ativos B3 carregados de fonte verificável. | Fechamento ou indisponível. |
| `GET /market/assets/{symbol}` | Consulta detalhe e último fechamento do ativo. | Fechamento ou indisponível. |
| `GET /market/assets/{symbol}/history` | Retorna série histórica diária com proveniência. | Fechamento. |
| `GET /market/btc` | Obtém último preço conhecido de BTC/USDT. | Tempo real quando o stream está ativo; fallback REST identificado. |
| `GET /macro/selic` | Retorna Selic da série oficial configurada. | Oficial. |

O carregamento B3 suporta até 15 anos por execução manual e persistência idempotente. O processo foi dividido em lotes seguros para não exceder limites de parâmetros do PostgreSQL durante o backfill.

### Atualização gratuita e automação

Foram adicionados dois fluxos de GitHub Actions sem Background Worker pago: uma sincronização diária de fechamento B3 e uma varredura de alertas a cada três horas. O modelo mantém o custo operacional dentro da combinação Render Free e GitHub Free, com a ressalva de que cotações B3 intradiárias licenciadas não são fornecidas por COTAHIST.

O radar de alertas Telegram foi preservado, incluindo preferências de alerta, canais padrão, controles de status e normalização de contadores legados.

## Correções aplicadas nesta entrega

| Correção | Problema resolvido | Efeito prático |
|---|---|---|
| Classificação B3 de FIIs e ETFs | O COTAHIST pode marcar fundos sob a especificação genérica `CI`, produzindo `fund_or_etf`. | HGLG11, KNRI11, MXRF11, XPLG11 e BCFF11 passam a ser exibidos como FIIs; BOVA11, IVVB11 e SMAL11 como ETFs. |
| Atualização do catálogo já carregado | A classificação precisava ser reaplicável para registros existentes. | A próxima sincronização B3 atualiza o `asset_class` idempotentemente no catálogo persistido. |
| Resumos de categoria com dados oficiais | Cards de ações, FIIs, ETFs e BDRs mostravam apenas resumo demonstrativo. | Os mesmos cards existentes passam a consultar o catálogo verificado e informar a fonte B3. |
| Atualização automática no frontend | Consultas verificadas tinham frequência maior do que o necessário para o requisito operacional. | Tabelas e resumos de ativos verificados consultam a API a cada 60 segundos. |
| Ferramentas com catálogo híbrido rastreável | Rankings, rastreador, comparador, carteira e busca usavam apenas o catálogo local. | Fechamentos B3 verificados substituem o mesmo ticker; itens sem cobertura mantêm selo demonstrativo. |
| Lotes de histórico B3 | Backfill de 15 anos podia exceder o limite de parâmetros em upserts grandes. | Inserções particionadas em lotes seguros de até 2.000 candles. |
| Contadores de heartbeat legados | Valores `NULL` provocavam erro ao somar contadores durante o agendamento. | Contadores são normalizados antes de incremento. |
| Exportação estática do portal | Rotas do Next.js não eram distribuídas corretamente ao FastAPI em produção. | Páginas são exportadas como índices de diretório e atendidas pelo portal publicado. |
| Cabeçalhos de segurança HTTP | A produção não adicionava proteções defensivas consistentes às respostas. | Inclusão de `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` e HSTS em produção. |

## Validação executada

> A checagem completa do backend foi executada com `DATABASE_URL` vazio no ambiente local de testes. Isso é intencional: o ambiente de sandbox injeta uma URL MySQL que não corresponde ao driver PostgreSQL do serviço Render. O problema é de configuração local de teste, não de produção; com banco desabilitado, os testes unitários isolados passaram integralmente.

| Verificação | Resultado | Detalhes |
|---|---|---|
| Parser e classificação COTAHIST | Aprovado | Ações, FIIs, ETFs e fallback genérico cobertos por teste. |
| Suíte backend | Aprovada | 38 testes, incluindo alertas, notificações, contratos de mercado, exportação estática e segurança. |
| Suíte frontend | Aprovada | 7 testes, incluindo priorização de fonte oficial. |
| Tipagem TypeScript | Aprovada | `tsc --noEmit` sem erros. |
| Build frontend | Aprovada | Exportação estática de 28 páginas. |
| Rotas publicadas | Aprovada | 26 rotas de UI responderam `200` após seguir redirecionamento. |
| Limites da API | Aprovada | Limites inválidos retornaram `422`; ativo inexistente retornou `404`. |

## Limitações conhecidas e transparência

O COTAHIST é um arquivo histórico público de fechamento; ele não substitui um feed B3 intradiário licenciado. Portanto, ações, FIIs e ETFs B3 devem continuar sendo descritos como **fechamento oficial**, não como tempo real. [1]

Fundamentos corporativos completos — como P/L, P/VP, DY, ROE, ROIC e EV/EBITDA verificados — ainda dependem da integração planejada com dados regulatórios da CVM e tratamento de períodos contábeis. A página de dividendos permanece conscientemente vazia até que existam datas e valores verificáveis; nenhum provento é inventado.

As classes sem fonte equivalente validada permanecem identificadas como demonstrativas. A cobertura atual de B3 em produção, no momento da auditoria, é de 18 ativos do universo monitorado. A classificação corrigida será persistida no próximo fluxo B3 após a aplicação deste patch.

## Aplicação do patch portátil

No PowerShell, abra **o repositório clonado**, não a pasta Downloads:

```powershell
cd $HOME\Documents\marketmind
Copy-Item "$HOME\Downloads\marketmind-verified-data-audit.patch" .
git am .\marketmind-verified-data-audit.patch
git push origin main
git log --oneline -1
```

Após o `push`, o Render inicia o deploy automático. Em seguida, execute manualmente o workflow **B3 free closing sync** uma vez com a lista padrão vazia e `years=1`, ou aguarde a próxima execução programada. Isso reaplica a classificação corrigida aos ativos já persistidos, sem duplicar candles.

## Segurança operacional pendente

Tokens de acesso que tenham sido enviados em conversas anteriores devem ser revogados no painel de tokens do GitHub e substituídos por credenciais novas, com escopo mínimo e armazenamento exclusivo em segredos do GitHub/Render. Nenhum token, senha ou URL de banco foi incluído nesta entrega.

## Referências

[1] [B3 — Cotações históricas do mercado à vista](https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/historico/mercado-a-vista/cotacoes-historicas/)

[2] [Banco Central do Brasil — Sistema Gerenciador de Séries Temporais](https://www.bcb.gov.br/estabilidadefinanceira/serieshistoricas)

[3] [Binance Spot API — documentação oficial](https://developers.binance.com/docs/binance-spot-api-docs)
