"use client";

import { useEffect, useRef, useState } from "react";
import clsx from "clsx";

interface PriceCardProps {
  label: string;
  value: string;
  delta?: string;
  deltaDirection?: "up" | "down" | "flat";
  sublabel?: string;
  live?: boolean;
  loading?: boolean;
}

/**
 * Card de cotação estilo terminal: número tabular grande, variação colorida,
 * flash sutil de fundo a cada atualização de preço (padrão de tickers reais).
 */
export function PriceCard({
  label,
  value,
  delta,
  deltaDirection = "flat",
  sublabel,
  live,
  loading,
}: PriceCardProps) {
  const [flash, setFlash] = useState(false);
  const prevValue = useRef(value);

  useEffect(() => {
    if (prevValue.current !== value) {
      setFlash(true);
      prevValue.current = value;
      const timeout = setTimeout(() => setFlash(false), 350);
      return () => clearTimeout(timeout);
    }
  }, [value]);

  return (
    <div
      className={clsx(
        "rounded-sm border border-terminal-border bg-terminal-panel p-4 transition-colors duration-300",
        flash && (deltaDirection === "down" ? "bg-down/10" : "bg-up/10")
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs uppercase tracking-wider text-terminal-muted font-mono">
          {label}
        </span>
        {live && (
          <span className="flex items-center gap-1.5">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-up opacity-75" />
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-up" />
            </span>
            <span className="text-[0.65rem] text-up font-mono tracking-wide">LIVE</span>
          </span>
        )}
      </div>

      <div className="mt-2 flex items-baseline gap-2">
        {loading ? (
          <div className="h-8 w-32 animate-pulse rounded bg-terminal-border" />
        ) : (
          <span className="tabular-tick font-mono text-2xl font-semibold text-terminal-text">
            {value}
          </span>
        )}
        {delta && (
          <span
            className={clsx(
              "tabular-tick font-mono text-sm font-medium",
              deltaDirection === "up" && "text-up",
              deltaDirection === "down" && "text-down",
              deltaDirection === "flat" && "text-terminal-muted"
            )}
          >
            {delta}
          </span>
        )}
      </div>

      {sublabel && (
        <div className="mt-1 text-xs text-terminal-muted font-mono">{sublabel}</div>
      )}
    </div>
  );
}
