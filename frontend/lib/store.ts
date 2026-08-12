import { create } from "zustand";
import type { PriceTick } from "./api";

interface MarketState {
  btcTick: PriceTick | null;
  wsStatus: "connecting" | "open" | "closed";
  setBtcTick: (tick: PriceTick) => void;
  setWsStatus: (status: "connecting" | "open" | "closed") => void;
}

export const useMarketStore = create<MarketState>((set) => ({
  btcTick: null,
  wsStatus: "connecting",
  setBtcTick: (tick) => set({ btcTick: tick }),
  setWsStatus: (status) => set({ wsStatus: status }),
}));
