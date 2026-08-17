import { Suspense } from "react";
import { AssetDetailView } from "@/components/asset-detail-view";

export default function AtivoPage() {
  return <Suspense fallback={null}><AssetDetailView /></Suspense>;
}
