"use client";

import { useEffect, useRef } from "react";
import {
  createChart,
  ColorType,
  IChartApi,
  ISeriesApi,
  UTCTimestamp,
} from "lightweight-charts";

interface BtcChartProps {
  data: Array<{ time: string; value: number }>;
  height?: number;
}

/**
 * Gráfico de linha estilo TradingView para o preço do BTC.
 * Recebe uma série já normalizada (time ISO + value) e cuida do resize.
 */
export function BtcChart({ data, height = 320 }: BtcChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Area"> | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const chart = createChart(containerRef.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#5c6b78",
        fontFamily: "'IBM Plex Mono', monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "#1e2833" },
        horzLines: { color: "#1e2833" },
      },
      rightPriceScale: {
        borderColor: "#1e2833",
      },
      timeScale: {
        borderColor: "#1e2833",
        timeVisible: true,
      },
      crosshair: {
        vertLine: { color: "#3ba7ff", labelBackgroundColor: "#3ba7ff" },
        horzLine: { color: "#3ba7ff", labelBackgroundColor: "#3ba7ff" },
      },
    });

    const series = chart.addAreaSeries({
      lineColor: "#26d07c",
      topColor: "rgba(38, 208, 124, 0.28)",
      bottomColor: "rgba(38, 208, 124, 0.02)",
      lineWidth: 2,
      priceLineVisible: false,
    });

    chartRef.current = chart;
    seriesRef.current = series;

    const handleResize = () => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    };
    handleResize();
    window.addEventListener("resize", handleResize);

    return () => {
      window.removeEventListener("resize", handleResize);
      chart.remove();
    };
  }, [height]);

  useEffect(() => {
    if (!seriesRef.current || data.length === 0) return;
    const formatted = data.map((d) => ({
      time: (new Date(d.time).getTime() / 1000) as UTCTimestamp,
      value: d.value,
    }));
    seriesRef.current.setData(formatted);
    chartRef.current?.timeScale().fitContent();
  }, [data]);

  return <div ref={containerRef} className="w-full" />;
}
