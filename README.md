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
6. O repositório inclui `render.yaml` na raiz: se preferir, use "New Blueprint Instance" no Render apontando para o repo e ele já configura Root Directory, build e start automaticamente.
7. O app agora sobe mesmo sem banco disponível no primeiro deploy (falha de conexão ao Postgres é logada, não derruba o processo); rotas que dependem de banco retornarão erro até `DATABASE_URL` estar correto.

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
3. **Alertas Telegram/WhatsApp** — notificações automáticas de mudança de tendência e cruzamento de indicadores.
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
