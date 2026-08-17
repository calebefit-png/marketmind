# Matriz de Cobertura de Dados — MarketMind

> **Status:** arquitetura de dados proposta; nenhuma linha abaixo autoriza rotular uma cotação como em tempo real sem fonte, horário e direitos de uso confirmados.

## Convenções de estado

| Estado exibido | Critério técnico | Exemplo de interface |
|---|---|---|
| `ao_vivo` | Evento recebido em stream ou consulta atualizada dentro da janela definida pela fonte | "Ao vivo · Binance · 12:34:56 UTC" |
| `atrasado` | Fonte informa preço com atraso, ou a última atualização ultrapassa a janela de atividade | "15 min de atraso · fonte identificada" |
| `fechamento` | Sessão encerrada ou série oficial diária | "Fechamento de 14/08/2026" |
| `regulatorio` | Dado oriundo de ITR, DFP, informe de fundo ou outro documento oficial | "ITR 2T26 · entregue em 14/08/2026" |
| `indisponivel` | Não há fonte válida, ativa ou licenciada | "Sem cobertura verificável" |

## Cobertura mínima por classe

| Classe | Catálogo e identidade | Histórico de 15 anos | Atualização de preço | Eventos, fundamentos e proventos | Fonte de referência | Situação inicial |
|---|---|---|---|---|---|---|
| Ações B3 | Ticker, ISIN e emissor | COTAHIST da B3 desde 1986; sujeito à existência do ativo | Provedor licenciado ou dado explicitamente atrasado | CVM DFP/ITR/FRE e eventos corporativos | B3 + CVM | Histórico oficial viável; live exige licença/provedor |
| FIIs | Ticker, CNPJ e administrador | COTAHIST quando negociado; vida do fundo pode ser menor que 15 anos | Provedor licenciado ou dado explicitamente atrasado | Informes CVM, dividendos e vacância | B3 + CVM | Histórico e informes viáveis; live exige licença/provedor |
| ETFs/BDRs | Ticker, ISIN e emissor/fundo | COTAHIST quando negociado; vida do ativo pode ser menor que 15 anos | Provedor licenciado ou dado explicitamente atrasado | Dados do emissor, B3 e CVM quando aplicável | B3 + CVM | Depende da existência e da fonte específica |
| Fundos, Fiagros e FIDCs | CNPJ, classe e administrador | Informes e cota de fundo conforme datas de registro | Geralmente por cota/informe, não stream de bolsa | CVM: cadastro, carteira, relatório e informe | CVM | Cobertura regulatória, com periodicidade própria |
| Tesouro Direto e renda fixa pública | Código de título e vencimento | Apenas desde o lançamento/listagem de cada título | Fonte oficial ou provedor que distribua as curvas | Taxas, preços e vencimentos | Tesouro/Provedor especializado | Não há quinze anos para títulos recém-criados |
| Criptoativos | Identificador de moeda e/ou par de corretora | Conforme lançamento do ativo e disponibilidade da exchange | WebSocket de exchange ou API agregada contratada | Métricas de mercado separadas de preço por corretora | Binance/CoinGecko | Live para pares Binance; agregado depende da fonte |
| Moedas e macro | Código ISO e código SGS | Séries do BCB conforme série histórica | Periodicidade oficial da série, não streaming de bolsa | Metadados, unidade e revisões do BCB | BCB SGS | Histórico longo para diversas séries |
| Índices e commodities | Código da série, bolsa ou índice | Conforme fornecedor e data de criação | Fonte licenciada ou com atraso explícito | Metodologia, composição e rolagem de contrato quando aplicável | B3/fornecedor licenciado/BCB | Requer contrato de dados para cobertura comercial ampla |
| Stocks e REITs globais | ISIN/ticker/bolsa | Conforme provedor internacional e idade do ativo | Provedor internacional licenciado | Filings e ações corporativas por jurisdição | A definir por licença | Não cobrir com dados demonstrativos |

## Regras de histórico

1. **Quinze anos é uma meta de janela, não uma promessa artificial por ativo.** Ativos listados há menos de quinze anos mostrarão apenas seu período real de negociação, com data de início aparente.
2. **Preço nominal e retorno total são séries diferentes.** O COTAHIST não ajusta inflação ou proventos; o retorno total só será habilitado depois de validar eventos corporativos e a política de ajuste.
3. **Fundamentos usam data de competência.** Um indicador mostra o trimestre/exercício a que pertence e não será recalculado com informação futura.
4. **Cada ponto armazenado traz proveniência.** Fonte, identificador externo, horário de coleta, data de referência, método de ajuste e checksum de carga serão persistidos.
5. **Não haverá fallback silencioso.** Se uma fonte ao vivo falhar, a interface muda de estado e exibe o último dado recebido; nunca inventa uma cotação atual.

## Decisão de produto pendente

Para cotações B3 de ampla cobertura com atualização ao vivo, a fonte precisa oferecer direitos de redistribuição e uma credencial de produção. As fontes abertas confirmadas resolvem o histórico oficial e vários fundamentos, mas não substituem esse requisito de licença para preço B3 em streaming. A implementação será dividida em:

1. base pública e verificável: B3 histórica, CVM, BCB e Binance;
2. adaptadores de provedores com credenciais configuráveis;
3. ativação de dados ao vivo por classe somente depois de validar fonte, limite e permissão de uso.
