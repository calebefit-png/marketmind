-- 001_create_candles.sql
-- Cria a tabela de candles em PostgreSQL comum e usa recursos TimescaleDB somente
-- quando a extensão estiver instalada. Isso mantém o desenvolvimento local e o
-- PostgreSQL gerenciado do Render compatíveis.

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

CREATE INDEX IF NOT EXISTS ix_candles_asset_timeframe_time
    ON candles (asset, timeframe, time DESC);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_available_extensions WHERE name = 'timescaledb'
    ) THEN
        BEGIN
            CREATE EXTENSION IF NOT EXISTS timescaledb;
            PERFORM create_hypertable(
                'candles',
                'time',
                if_not_exists => TRUE,
                migrate_data => TRUE
            );
            EXECUTE 'ALTER TABLE candles SET (timescaledb.compress, timescaledb.compress_segmentby = ''asset,timeframe'')';
            PERFORM add_compression_policy(
                'candles', INTERVAL '30 days', if_not_exists => TRUE
            );
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'TimescaleDB disponível, mas recursos opcionais não foram ativados: %', SQLERRM;
        END;
    ELSE
        RAISE NOTICE 'TimescaleDB não disponível; usando PostgreSQL padrão para candles.';
    END IF;
END
$$;
