import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/lib/query-provider";

export const metadata: Metadata = {
  title: "MarketMind Intelligence — Portal de Investimentos",
  description:
    "Portal de inteligência financeira com classes de investimento, indicadores, rankings, rastreadores, comparadores, carteira, macro e alertas operacionais.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body className="font-sans antialiased bg-portal-canvas text-portal-ink min-h-screen">
        <QueryProvider>{children}</QueryProvider>
      </body>
    </html>
  );
}
