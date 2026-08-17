# MarketMind AI

Plataforma de inteligência financeira com IA: monitoramento em tempo real de criptomoedas, ações brasileiras, fundos imobiliários e indicadores macroeconômicos, com detecção automática de padrões técnicos e análises probabilísticas de tendência.

> **Aviso:** o sistema trabalha exclusivamente com probabilidades e cenários. Nenhum endpoint promete rentabilidade ou prevê resultados garantidos. Nada aqui constitui recomendação de investimento.

---

## Deploy rápido

### Backend no Render

1. Novo Web Service → conectar o repositório.
2. **Root Directory:** `backend`
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Variáveis de ambiente obrigatórias (Render → Environment): `DATABASE_URL`, `DATABASE_URL_SYNC`, `REDIS_URL`, `CORS_ORIGINS` (URL do frontend no Netlify), `APP_ENV=production`, `APP_DEBUG=false`.
6. Configure o Web Service manualmente com os campos acima. Um processo de alertas deve ser criado separadamente conforme a seção de alertas abaixo.
7. O app agora sobe mesmo sem banco disponível no primeiro deploy (falha de conexão ao Postgres é logada, não derruba o processo); rotas que dependem de banco retornarão erro até `DATABASE_URL` estar correto.

### Portal servido pelo mesmo Web Service

O FastAPI entrega a exportação estática do portal diretamente a partir de `backend/static`. Como o serviço gratuito do Render está definido com **Root Directory `backend`** e runtime Python, ele não compila o Next.js durante o deploy. Por isso, qualquer mudança visual deve ser exportada e incluída no commit antes do `git push`:

```bash
./scripts/build_static_frontend.sh
git add backend/static
git commit -m "build: publish frontend static export"
git push origin main
```

O script instala as dependências travadas do frontend, executa a build de produção e substitui `backend/static` pela pasta `frontend/out`. Não copie arquivos manualmente, não envie `frontend/out` ao repositório e não inclua variáveis de ambiente ou segredos nesse processo.

### Frontend no Netlify

1. Novo site → conectar o repositório.
2. **Base directory:** `frontend`
3. **Build command:** `npm run build` (já configurado em `frontend/netlify.toml`, que inclui `@netlify/plugin-nextjs`)
4. **Variável de ambiente:** `NEXT_PUBLIC_API_URL` = URL pública do backend no Render (ex.: `https://marketmind-backend.onrender.com`).
5. O WebSocket é derivado automaticamente de `NEXT_PUBLIC_API_URL` (`https→wss`, `http→ws`); não é necessário configurar `NEXT_PUBLIC_WS_URL` separadamente, a menos que o WS rode em host diferente do REST.

### Variáveis de ambiente

- `backend/.env.example` → copiar para `backend/.env` em desenvolvimento local.
- `frontend/.env.example` → copiar para `frontend/.env.local` em desenvolvimento local.

---

## Stack

**Frontend:** Next.js 15, TypeScript, Tailwind CSS, TradingView Lightweight Charts, Zustand, React Query
**Backend:** Python 3.12, FastAPI, WebSocket, pandas, numpy, scikit-learn, `ta`, SQLAlchemy 2.0 (async), Pydantic v2
**Banco:** PostgreSQL + TimescaleDB (hypertables)
**Infra:** Docker + Docker Compose

---

## Estrutura do projeto

```
marketmind/
├── frontend/                  # Next.js 15 (App Router)
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── dashboard.tsx
│   │   ├── price-card.tsx
│   │   └── btc-chart.tsx
│   ├── lib/
│   │   ├── api.ts
│   │   ├── store.ts
│   │   └── query-provider.tsx
│   ├── package.json
│   ├── tailwind.config.ts
│   └── Dockerfile
├── backend/                   # FastAPI
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/candle.py
│   ├── schemas/candle.py
│   ├── services/
│   │   ├── binance_stream.py
│   │   ├── bcb_service.py
│   │   ├── technical_analysis.py
│   │   ├── trend_engine.py
│   │   └── ws_manager.py
│   ├── api/routes/market.py
│   ├── migrations/001_create_candles.sql
│   ├── scripts/seed_btc_history.py
│   ├── requirements.txt
│   └── Dockerfile
├── infrastructure/
├── docs/
└── docker-compose.yml
```

---

## Requisitos

- Docker e Docker Compose
- Node.js 20+ (apenas se rodar o frontend fora do container)
- Python 3.12+ (apenas se rodar o backend fora do container)

---

## Instalação e execução

### 1. Variáveis de ambiente

```bash
cp backend/.env.example backend/.env
```

Ajuste os valores se necessário (padrões já funcionam com o `docker-compose.yml`).

### 2. Subir todos os serviços

```bash
docker compose up --build
```

Isso inicia:
- `postgres` (TimescaleDB) na porta `5432`
- `redis` na porta `6379`
- `backend` (FastAPI) na porta `8000`
- `frontend` (Next.js) na porta `3000`

A migration `001_create_candles.sql` roda automaticamente na primeira subida do container Postgres, criando a hypertable `candles`.

### 3. Popular histórico do BTC (1 ano de candles diários)

Com o backend já rodando (via Docker ou local):

```bash
docker compose exec backend python -m scripts.seed_btc_history
```

Ou localmente, dentro de `backend/` com um venv ativo:

```bash
pip install -r requirements.txt --no-cache-dir
python -m scripts.seed_btc_history
```

### 4. Acessar

- Frontend: http://localhost:3000
- Backend (docs Swagger): http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

## Endpoints disponíveis

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Status da aplicação |
| GET | `/market/btc` | Último preço BTC/USDT (stream Binance, fallback REST) |
| GET | `/macro/selic` | Taxa Selic atual, data de referência e variação (API SGS do BCB) |
| GET | `/analysis/btc` | Indicadores técnicos + classificação de tendência heurística (ALTA/BAIXA/LATERAL) e score 0-100 |
| GET | `/prediction/{asset}?horizon=24` | Predição estatística via modelo treinado (GBM + walk-forward); retorna `model_not_reliable` se abaixo dos critérios mínimos |
| WS | `/ws/market` | Streaming de ticks de preço em tempo real (`{"type": "price_tick", "data": {...}}`) |

Todas as rotas também respondem sob o prefixo `/api/v1` (ex.: `/api/v1/market/btc`).

---

## Alertas por Gmail API com OAuth 2.0

O backend utiliza exclusivamente a **Gmail API oficial** com OAuth 2.0 e o escopo mínimo `https://www.googleapis.com/auth/gmail.send`. Não há SMTP, senha Gmail, App Password, Service Account nem integração funcional com Resend. O refresh token permanece somente nas variáveis de ambiente do Render e é renovado pela biblioteca oficial do Google.[1] [2]

| Variável | Finalidade |
| --- | --- |
| `GOOGLE_CLIENT_ID` e `GOOGLE_CLIENT_SECRET` | Credenciais de um cliente OAuth Web criado no Google Cloud |
| `GOOGLE_REFRESH_TOKEN` | Autorização persistente para enviar em nome da conta Gmail; nunca versionar |
| `GMAIL_SENDER_EMAIL` | Conta Google que autorizou o envio de alertas |
| `GMAIL_ADMIN_SECRET` | Protege o início do OAuth, o `state` assinado e o envio administrativo de teste |
| `GMAIL_OAUTH_REDIRECT_URI` | URI de callback registrada no Google Cloud Console |
| `GMAIL_STATE_MAX_AGE_SECONDS` | Validade do `state` HMAC do OAuth, com padrão de 600 segundos |

### Google Cloud Console

No [Google Cloud Console](https://console.cloud.google.com/), crie ou selecione um projeto dedicado ao MarketMind. Abra **APIs e serviços → Biblioteca**, procure por **Gmail API** e clique em **Ativar**. Em **APIs e serviços → Tela de consentimento OAuth**, escolha o tipo de público apropriado. Para uma conta pessoal em teste, escolha **Externo**, preencha os campos obrigatórios e inclua a conta remetente em **Test users**.

Em **Escopos**, adicione somente `https://www.googleapis.com/auth/gmail.send`. Esse escopo permite enviar e-mails em nome da conta que consentiu a autorização.[2] Em **Credenciais → Criar credenciais → ID do cliente OAuth**, escolha **Aplicativo da Web** e cadastre esta URI de redirecionamento autorizada:

```text
https://marketmind-l3kg.onrender.com/auth/gmail/callback
```

Para desenvolvimento local, cadastre adicionalmente a URI local definida por `GMAIL_OAUTH_REDIRECT_URI`, por exemplo `http://localhost:8000/auth/gmail/callback`. Copie o Client ID e o Client secret, mas não os registre em repositórios, arquivos de exemplo ou canais de comunicação.

### Render, autorização e teste

No Render, em **Environment**, cadastre `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GMAIL_SENDER_EMAIL`, `GMAIL_ADMIN_SECRET` e `GMAIL_OAUTH_REDIRECT_URI=https://marketmind-l3kg.onrender.com/auth/gmail/callback`. Para o segredo administrativo, gere um valor aleatório longo com:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Inicialmente, deixe `GOOGLE_REFRESH_TOKEN` ausente. Após o deploy dessas variáveis, inicie o OAuth sem colocar o segredo na URL:

```bash
curl --silent --show-error --include \
  --header "X-Gmail-Admin-Secret: SEU_GMAIL_ADMIN_SECRET" \
  https://marketmind-l3kg.onrender.com/auth/gmail
```

Copie a URL do cabeçalho `location:` para o navegador, faça login na conta remetente e clique em **Permitir**. O callback revela o refresh token somente uma vez pela conexão HTTPS, com `Cache-Control: no-store`; copie-o imediatamente para `GOOGLE_REFRESH_TOKEN` no Render e faça novo deploy. O código não persiste esse token em arquivos, banco ou logs.

Após o redeploy, valide uma entrega real pelo endpoint administrativo protegido:

```bash
curl --request POST https://marketmind-l3kg.onrender.com/auth/gmail/test \
  --header "Content-Type: application/json" \
  --header "X-Gmail-Admin-Secret: SEU_GMAIL_ADMIN_SECRET" \
  --data '{"to":"seu-email-de-teste@example.com","subject":"Teste MarketMind","body":"A integração Gmail OAuth está ativa."}'
```

O serviço suporta texto, HTML, múltiplos destinatários, `Reply-To` e possui contrato para anexos. O endpoint de teste não devolve corpo nem destinatário na resposta. Mantenha `GMAIL_ADMIN_SECRET`, `GOOGLE_CLIENT_SECRET` e `GOOGLE_REFRESH_TOKEN` apenas no cofre de variáveis do Render.

> Dois tokens pessoais do GitHub foram compartilhados durante o desenvolvimento. Por segurança, revogue-os imediatamente em [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens), mesmo que não estejam no repositório.

Para verificar localmente, entre em `backend`, instale as dependências e execute `python -m unittest discover -s tests -v`.

---

## Alertas Telegram e worker de mercado

O MarketMind possui um processo de alertas separado da API HTTP. Ele recebe ticks verificáveis de `BTCUSDT` via Binance, consulta candles diários já persistidos para calcular RSI, MACD, rompimentos e volume relativo, e verifica a série Selic já integrada ao BCB. A primeira entrega **não inventa** notícias, fluxo de baleias, Smart Money, dados B3, pesquisas BTG ou macro internacional: esses tópicos aguardam conectores de dados verificáveis.

| Categoria | Critério inicial | Deduplicação e entrega |
| --- | --- | --- |
| Preço | Movimento de ao menos `2,5%` em até 15 minutos, configurável. | Cooldown persistente padrão de 30 minutos por perfil, ativo e regra. |
| Técnica | RSI extremo, cruzamento MACD, rompimento diário de faixa de 20 candles e volume acima da média. | O texto informa hipótese, fonte e condição de invalidação; não recomenda comprar ou vender. |
| Macro Brasil | Mudança material na série Selic monitorada. | Cooldown de 24 horas para a mesma regra. |
| IA preditiva | Desabilitada enquanto o modelo estiver em `model_not_reliable`. | Nenhuma previsão não validada é enviada como alerta. |

### Criar e configurar o bot Telegram

Abra [@BotFather](https://t.me/BotFather), envie `/newbot`, defina o nome e o identificador do bot e guarde o token retornado somente no cofre de variáveis do Render. Em seguida, abra a conversa com o bot e envie `/start`. Para obter o identificador de conversa, defina temporariamente o token no seu terminal local e execute:

```bash
export TELEGRAM_BOT_TOKEN='token-fornecido-pelo-botfather'
curl --silent "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getUpdates"
```

Localize o campo `message.chat.id` na resposta. Em grupos, adicione o bot e envie uma mensagem de teste antes de consultar `getUpdates`. Não compartilhe o token ou a resposta integral em chats, logs ou repositórios. A Bot API usa HTTPS e devolve um objeto JSON com o campo `ok`; o provedor interno aplica timeout, retentativas limitadas, leitura de `retry_after`, fragmentação e um intervalo conservador por conversa.[3] [4]

No Render, cadastre `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `ADMIN_NOTIFICATION_SECRET` e `ALERT_DEFAULT_CHANNELS=telegram`. O Telegram é o único canal ativo do radar. As preferências de ativo, canal, severidade mínima, cooldown e pausa ficam no PostgreSQL; tokens, chat IDs e endereços de entrega nunca são persistidos nesse histórico.

O endpoint de teste é administrativo e não aparece no Swagger:

```bash
curl --request POST https://marketmind-l3kg.onrender.com/notifications/test/telegram \
  --header "Content-Type: application/json" \
  --header "X-Admin-Notification-Secret: SEU_ADMIN_NOTIFICATION_SECRET" \
  --data '{"message":"<b>MarketMind</b> — teste de Telegram."}'
```

### Operação sem serviço adicional no Render

Para manter a operação sem contratar um Background Worker no Render, o repositório inclui o workflow `.github/workflows/market-alert-sweep.yml`. Ele inicia uma varredura única a cada três horas e também pode ser executado manualmente em **Actions → Market alert sweep → Run workflow**. A varredura consulta os dados verificáveis disponíveis, processa os sinais técnicos e macroeconômicos, espera a fila Telegram terminar e grava o estado `scheduled` no heartbeat antes de encerrar.

No GitHub, em **Settings → Secrets and variables → Actions**, crie somente estes segredos de repositório: `DATABASE_URL`, `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`. Copie os mesmos valores já mantidos de forma privada no Render; não os escreva no workflow, no código, em commits ou em mensagens. O workflow não requer `ADMIN_NOTIFICATION_SECRET` porque não invoca as rotas administrativas.

> O agendamento é uma alternativa de menor custo, não um processo em tempo real. Ele pode detectar e enviar um alerta somente na próxima varredura e depende da disponibilidade do GitHub Actions e da franquia de execução da conta. Repositórios públicos têm execução padrão gratuita; em contas GitHub Free com repositórios privados há 2.000 minutos mensais incluídos e, sem método de pagamento, a execução é bloqueada ao atingir a franquia.[5]

O **Start Command** do Web Service gratuito deve permanecer `uvicorn main:app --host 0.0.0.0 --port $PORT`. Nunca substitua esse comando por `python -m services.alerts.alert_worker`, pois isso interrompe a API HTTP e o frontend.

### Processo contínuo pago no Render (opcional)

No mesmo repositório e com o mesmo `Root Directory` (`backend`), crie em **New → Background Worker** um serviço separado. Use `pip install -r requirements.txt` como **Build Command** e `python -m services.alerts.alert_worker` como **Start Command**. O `runtime.txt` fixa **Python 3.12**. Copie `DATABASE_URL`, as variáveis Binance/BCB, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `ADMIN_NOTIFICATION_SECRET` e as variáveis `ALERT_*` para esse Worker. O worker deve permanecer em uma única réplica; a deduplicação, o cooldown e o heartbeat permanecem no PostgreSQL após reinicializações.

As preferências do perfil administrativo inicial podem ser consultadas ou atualizadas apenas com o segredo administrativo:

```bash
curl --request PUT https://marketmind-l3kg.onrender.com/notifications/preferences/owner \
  --header "Content-Type: application/json" \
  --header "X-Admin-Notification-Secret: SEU_ADMIN_NOTIFICATION_SECRET" \
  --data '{"assets":["BTCUSDT","SELIC"],"channels":["telegram"],"minimum_severity":"WARNING","cooldown_seconds":1800,"paused":false}'
```

O contrato operacional completo de fontes e limites está em [`docs/alert_event_coverage.md`](docs/alert_event_coverage.md). Para a API oficial do Telegram, mantenha como limite conservador no máximo uma mensagem por segundo por conversa; excedê-lo pode resultar em `429`.[4]

As rotas públicas `GET /alerts/status` e `GET /alerts/recent` exibem, respectivamente, o heartbeat sem segredos, a configuração do Telegram, a condição de confiabilidade do modelo e o histórico de alertas. O catálogo expõe Binance e BCB como fontes disponíveis; B3, BTG Research, News e Whales retornam explicitamente `not_available` até que conectores verificáveis sejam integrados.

### Central de alertas e filtros

A página `https://SEU_FRONTEND/alerts` concentra o histórico operacional do radar. Ela permite filtrar alertas por ativo, severidade, canal Telegram, status de entrega e intervalo de datas; o histórico é atualizado a cada 30 segundos e apresenta somente eventos persistidos pelo worker.

| Parâmetro público de `GET /alerts/recent` | Exemplo | Uso |
| --- | --- | --- |
| `asset` | `BTCUSDT` | Limita o histórico a um ativo monitorado. |
| `severity` | `WARNING` | Filtra por `INFO`, `WARNING` ou `CRITICAL`. |
| `channel` | `telegram` | Filtra pelo canal de entrega. |
| `status` | `sent` | Filtra por estado operacional do evento. |
| `date_from` e `date_to` | `2026-08-14T00:00:00Z` | Delimitam o período do histórico. |

Os controles globais mostrados na página — ativos, severidade mínima, cooldown e pausa — são somente leitura no navegador. A alteração permanece protegida pela API administrativa com `ADMIN_NOTIFICATION_SECRET`, evitando que esse segredo seja distribuído para o cliente. Nesta entrega, **Telegram é o único canal operacional**; o código de Gmail OAuth permanece isolado para uso futuro e não é exigido para iniciar, testar ou operar o Worker.

## Referências

[1] [Gmail API — Sending Email](https://developers.google.com/gmail/api/guides/sending)

[2] [Gmail API — OAuth 2.0 Scopes](https://developers.google.com/gmail/api/auth/scopes)

[3] [Telegram Bot API — Requests and responses](https://core.telegram.org/bots/api)

[4] [Telegram Bots FAQ — Broadcasting limits](https://core.telegram.org/bots/faq)

[5] [GitHub Actions — cobrança e franquias incluídas](https://docs.github.com/billing/managing-billing-for-github-actions/about-billing-for-github-actions)

---

## Fase 2 — Motor preditivo (IA estatística real)

Diferente do `trend_engine.py` (regras heurísticas fixas), o motor abaixo **aprende** com histórico via `GradientBoostingClassifier` e é validado com **walk-forward** (janelas anuais expansivas, nunca embaralhadas).

### Pipeline

```
backend/
├── services/
│   ├── feature_engineering.py   # 24 features: retorno, momentum, SMA9/21/50,
│   │                             # RSI, MACD, estocástico, ATR, std20, vol.
│   │                             # anualizada, volume relativo/z-score, regime
│   ├── label_engine.py          # target multiclasse ALTA/BAIXA/LATERAL,
│   │                             # baseado no retorno N candles à frente
│   ├── predictive_model.py      # train_walk_forward_model + critérios mínimos
│   └── model_registry.py        # persiste/carrega model + label_encoder + metadata/metrics
├── scripts/
│   ├── train_model.py           # pipeline de treino offline completo
│   └── evaluate_model.py        # métricas + matriz de confusão por fold
├── models_store/BTCUSDT/        # model.joblib, label_encoder.joblib,
│                                 # metrics.json, metadata.json
└── api/routes/prediction.py     # GET /prediction/{asset}
```

### Treinar o modelo

```bash
cd backend
python scripts/train_model.py --asset BTCUSDT --timeframe 1d --horizon 24
```

Gera:

```
backend/models_store/BTCUSDT/model.joblib
backend/models_store/BTCUSDT/label_encoder.joblib
backend/models_store/BTCUSDT/metrics.json
backend/models_store/BTCUSDT/metadata.json
```

Flags opcionais: `--threshold 0.015` (limiar de retorno para ALTA/BAIXA) e `--min-train-years 5` (anos mínimos de treino antes do primeiro fold de teste). Reduza `--min-train-years` (ex.: `2`) logo após o seed de 1 ano de histórico — o walk-forward exige `min_train_years + 1` anos de dado para gerar ao menos um fold; sem isso o script falha explicitamente em vez de produzir um resultado inválido silenciosamente.

### Avaliar um modelo já treinado (sem retreinar)

```bash
python scripts/evaluate_model.py --asset BTCUSDT
```

Imprime metadata, métricas agregadas e, para cada fold de walk-forward, a matriz de confusão (linhas = classe real, colunas = classe prevista).

### Critérios mínimos de confiabilidade

O modelo só é exibido ao usuário se, na média dos folds de walk-forward:

- balanced accuracy > **0.52**
- F1 macro > **0.50**
- retorno médio por sinal acionável (ALTA/BAIXA) > **0**
- pelo menos **3 anos** de teste out-of-sample cobertos

Se algum critério falhar, `GET /prediction/{asset}` retorna `status: "model_not_reliable"` com as métricas e critérios exatos, em vez de expor uma previsão não confiável.

### Endpoint

```
GET /prediction/BTCUSDT?horizon=24&timeframe=1d
```

```json
{
  "asset": "BTCUSDT",
  "horizon_candles": 24,
  "generated_at": "2026-08-11T12:00:00Z",
  "prediction": "ALTA",
  "probabilities": { "ALTA": 0.64, "LATERAL": 0.22, "BAIXA": 0.14 },
  "model": {
    "name": "btcusdt_gbm_v1",
    "trained_until": "2026-08-10",
    "backtest_balanced_accuracy": 0.58,
    "backtest_f1_macro": 0.55,
    "oos_years_covered": 4
  },
  "confidence_band": { "lower": 0.56, "upper": 0.71 },
  "disclaimer": "Probabilidades estatísticas baseadas em histórico; não constituem recomendação de investimento."
}
```

Deliberadamente **fora** de escopo nesta fase (complexidade desnecessária antes de provar valor do baseline): LSTM/Transformer, reinforcement learning, predição tick a tick, ensemble complexo, GPU.

---

## Roadmap técnico

1. **Ações B3 em tempo real** — integração com provedor de cotações B3 (ex.: Alpha Vantage, Brapi, ou feed direto) para PETR4, VALE3, ITUB4 etc.
2. **IFIX e FIIs** — monitoramento do índice IFIX e principais fundos imobiliários.
3. **WhatsApp e conectores de fontes adicionais** — canal complementar, B3 em tempo real, notícias, whale activity e outros eventos somente após integração de fontes verificáveis.
4. **Backtesting** — motor de simulação histórica das estratégias de tendência sobre dados armazenados no TimescaleDB.
5. **LSTM/Transformer** — modelos de séries temporais para previsão probabilística de curto prazo, substituindo/complementando o motor de regras atual.
6. **Sentimento de notícias** — pipeline de NLP sobre notícias financeiras para score de sentimento por ativo.
7. **Carteira do usuário** — autenticação, portfólio pessoal, tracking de posições e P&L.
8. **Deploy AWS/GCP** — infraestrutura como código (Terraform), CI/CD, observabilidade (Grafana + Prometheus) e escalonamento do TimescaleDB.

---

## Notas de arquitetura

- O `BinanceStreamService` mantém uma única conexão WebSocket persistente com a Binance e faz *fan-out* para todos os clientes conectados via `ConnectionManager`, evitando múltiplas conexões upstream.
- `services/trend_engine.py` implementa um modelo de score linear simples (combinação ponderada de gap de médias móveis e RSI). É um ponto de partida deliberadamente interpretável — o item 5 do roadmap substitui/complementa por modelos estatísticos mais robustos.
- A tabela `candles` é uma hypertable do TimescaleDB particionada por tempo, com política de compressão automática após 30 dias, adequada para séries históricas de longo prazo.
- Todas as análises retornam probabilidades e scores, nunca certezas — reflexo direto do requisito de não prometer rentabilidade.
