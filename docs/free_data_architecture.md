# Arquitetura de Dados Gratuita e Verificável

## Objetivo operacional

O modo gratuito entrega dados realmente obtidos das fontes públicas disponíveis, preservando o significado de cada atualização. Ele não tenta reproduzir um feed comercial de bolsa por meio de scraping, nem apresenta fechamento de pregão como se fosse preço em tempo real.

| Domínio | Fonte inicial | Modalidade | Atualização | Persistência |
|---|---|---|---|---|
| Cripto por par de corretora | Binance | WebSocket, com REST de contingência | Contínua enquanto o serviço estiver ativo; REST ao solicitar | Tick corrente e candles OHLCV |
| Ações, FIIs, ETFs e BDRs B3 | COTAHIST público da B3 | Arquivo diário/anual oficial | Após a publicação do arquivo oficial | OHLCV diário e metadados da sessão |
| Demonstrações, fundos e informes | CVM Dados Abertos | Arquivos e conjuntos regulatórios | Conforme a periodicidade do documento | Documento de origem, data de competência e valores normalizados |
| Juros, câmbio e macro | Banco Central do Brasil SGS | API pública | Conforme periodicidade da série | Pontos de série e metadados SGS |

## Componentes

O backend passa a separar quatro conceitos que hoje estão concentrados na tabela `candles`.

| Componente | Responsabilidade | Garantia principal |
|---|---|---|
| `Asset` | Identifica um instrumento por símbolo, classe, bolsa, país e identificadores externos | Não confundir tickers semelhantes de mercados diferentes |
| `DataPoint` | Guarda preço, candle, indicador ou métrica com data de referência | A série mantém fonte, estado e horário de coleta |
| `DataSource` | Descreve uma fonte, licença, URL, atraso e disponibilidade | A interface pode explicar de onde veio cada número |
| `IngestionRun` | Registra início, fim, resultado e checksum de cada carga | Reprocessamento idempotente e auditoria operacional |

## Estratégia de atualização

> **Criptoativos Binance:** o processo já existente de WebSocket permanece como feed ao vivo para os pares habilitados. Quando o stream estiver indisponível, o backend consulta o endpoint REST e altera a fonte exibida para `binance_rest`.

> **B3 no modo gratuito:** a carga usa arquivos públicos COTAHIST depois de publicados. A interface apresenta o campo `data_status=closing` e a data do pregão. O sistema não executará polling subminuto em arquivo histórico, pois isso não produz preço ao vivo e desperdiça recursos.

> **Agendamento B3:** em dias úteis, uma execução após o fechamento reconcilia o arquivo público do ano corrente para uma lista inicial de ações, FIIs e ETFs. Uma execução manual permite selecionar tickers e carregar de 1 a 15 anos de histórico. Todo ponto resultante permanece classificado como `closing`.

> **CVM e BCB:** cargas são determinísticas e baseadas na frequência real do documento ou série. Elas são executadas em ciclos agendados de baixa frequência e podem ser repetidas sem duplicar registros.

O agendamento será separado em tarefas de curta duração: atualização de macro, sincronização de arquivos B3 publicados e coleta de documentos regulatórios. A estratégia evita processo permanente para fontes que não fornecem eventos em tempo real e mantém compatibilidade com a operação gratuita existente.

## Contrato de dados para a interface

Cada resposta de mercado deve trazer, além do valor, os campos abaixo.

```json
{
  "asset": "PETR4",
  "value": 0,
  "as_of": "2026-08-14T00:00:00Z",
  "received_at": "2026-08-15T02:10:00Z",
  "data_status": "closing",
  "source": {
    "id": "b3_cotahist",
    "name": "B3 COTAHIST",
    "url": "https://www.b3.com.br/",
    "license_note": "Arquivo histórico público; não equivale a feed em tempo real."
  }
}
```

## Evolução para fonte licenciada

O contrato não será acoplado a uma API gratuita específica. Um provedor futuro só poderá preencher `data_status=live` para classes cobertas, se a credencial estiver configurada e a resposta trouxer horário e permissão de uso compatíveis. Em caso de expiração, erro ou limite de cota, a resposta retorna ao último dado armazenado e marca o estado corretamente.

## Limites declarados

Uma série de quinze anos será retornada somente quando o instrumento já existia e a fonte disponibiliza os dados. Fundos, ETFs, FIIs, BDRs, títulos e criptoativos criados mais recentemente exibem sua janela histórica real, com início explícito. Dados ajustados por proventos, desdobramentos e eventos corporativos serão publicados apenas depois de cada regra de ajuste ser validada contra a fonte documental correspondente.
