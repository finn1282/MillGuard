export type * from "@contracts/api";

// Contract v1.8 (notify). Kept local until contracts/api.ts ships it.
export interface NotifyStatus { enabled: boolean; channel?: string; subscribers?: number }
export interface NotifyOut { ok: boolean; sent: number }
