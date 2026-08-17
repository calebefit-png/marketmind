import { Suspense } from "react";
import { SearchPage } from "@/components/portal-pages";

export default function Page() {
  return <Suspense fallback={<div className="min-h-screen bg-portal-canvas" />}><SearchPage /></Suspense>;
}
