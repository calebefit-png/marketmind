-- 001_create_candles.sql
-- Cria a tabela `candles` e a converte em hypertable do TimescaleDB.
-- Executado automaticamente pelo container postgres na primeira inicialização
-- (montado em /docker-entrypoint-initdb.d).

CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS candles (
    asset       VARCHAR(20)  NOT NULL,
    timeframe   VARCHAR(10)  NOT NULL,
    time        TIMESTAMPTZ  NOT NULL,
    open        DOUBLE PRECISION NOT NULL,
    high        DOUBLE PRECISION NOT NULL,
    low         DOUBLE PRECISION NOT NULL,
    close       DOUBLE PRECISION NOT NULL,
    volume      DOUBLE PRECISION NOT NULL DEFAULT 0,
    PRIMARY KEY (asset, timeframe, time)
);

-- Converte em hypertable particionada pela coluna de tempo.
SELECT create_hypertable(
    'candles',
    'time',
    if_not_exists => TRUE,
    migrate_data => TRUE
);

CREATE INDEX IF NOT EXISTS ix_candles_asset_timeframe_time
    ON candles (asset, timeframe, time DESC);

-- Compressão nativa do TimescaleDB para dados antigos (> 30 dias), opcional em produção.
ALTER TABLE candles SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'asset,timeframe'
);

SELECT add_compression_policy('candles', INTERVAL '30 days', if_not_exists => TRUE);
