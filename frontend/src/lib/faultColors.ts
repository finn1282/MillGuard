import type { FaultClass } from "./types";

// One colour per fault class, used by the fault guide and the Machine page chip.
// accent = border/icon, tint = header/chip fill, ink = text on tint (AA checked by scripts/contrast.mjs).
export const FAULT_COLORS: Record<FaultClass, { accent: string; tint: string; ink: string }> = {
  worm_wear: { accent: "#D97706", tint: "#FEF3C7", ink: "#78350F" },
  bearing: { accent: "#8B5CF6", tint: "#EDE9FE", ink: "#4C1D95" },
  gearbox_shaft: { accent: "#3B82F6", tint: "#DBEAFE", ink: "#1E3A8A" },
  hydraulic_cone: { accent: "#06B6D4", tint: "#CFFAFE", ink: "#164E63" },
  electrical: { accent: "#EAB308", tint: "#FEF9C3", ink: "#713F12" },
  unknown: { accent: "#64748B", tint: "#F1F5F9", ink: "#1E293B" },
  boiler_steam: { accent: "#EF4444", tint: "#FEE2E2", ink: "#7F1D1D" },
  boiler_water: { accent: "#0EA5E9", tint: "#E0F2FE", ink: "#0C4A6E" },
};

export const faultColor = (fc: string) => FAULT_COLORS[fc as FaultClass] ?? FAULT_COLORS.unknown;
