import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/lib/query-provider";

export const metadata: Metadata = {
  title: "MarketMind AI — Terminal de Inteligência de Mercado",
  description:
    "Monitoramento em tempo real de criptomoedas, ações brasileiras, FIIs e indicadores macroeconômicos com análise técnica probabilística.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body className="font-sans antialiased bg-terminal-bg text-terminal-text min-h-screen">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
