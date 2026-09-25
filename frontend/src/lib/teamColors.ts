export const TEAM_COLORS: Record<string, { bg: string; text: string; hex: string; border: string }> = {
  McLaren: { bg: "bg-amber-500/20", text: "text-amber-400", hex: "#FF8000", border: "border-amber-500/40" },
  "Red Bull Racing": { bg: "bg-blue-600/20", text: "text-blue-400", hex: "#3671C6", border: "border-blue-500/40" },
  Ferrari: { bg: "bg-red-600/20", text: "text-red-500", hex: "#E8002D", border: "border-red-500/40" },
  Mercedes: { bg: "bg-emerald-400/20", text: "text-emerald-300", hex: "#27F4D2", border: "border-emerald-400/40" },
  Williams: { bg: "bg-sky-500/20", text: "text-sky-400", hex: "#64C4FF", border: "border-sky-400/40" },
  "Aston Martin": { bg: "bg-teal-700/20", text: "text-teal-400", hex: "#229971", border: "border-teal-500/40" },
  Alpine: { bg: "bg-pink-600/20", text: "text-pink-400", hex: "#0093CC", border: "border-pink-500/40" },
  RB: { bg: "bg-indigo-600/20", text: "text-indigo-400", hex: "#6692FF", border: "border-indigo-500/40" },
  "Haas F1 Team": { bg: "bg-zinc-500/20", text: "text-zinc-300", hex: "#B6BABD", border: "border-zinc-400/40" },
  "Kick Sauber": { bg: "bg-green-500/20", text: "text-green-400", hex: "#52E252", border: "border-green-500/40" },
};

export const COMPOUND_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  SOFT: { bg: "bg-red-500/20", text: "text-red-400", border: "border-red-500/40" },
  MEDIUM: { bg: "bg-yellow-500/20", text: "text-yellow-400", border: "border-yellow-500/40" },
  HARD: { bg: "bg-zinc-200/20", text: "text-zinc-200", border: "border-zinc-300/40" },
  INTERMEDIATE: { bg: "bg-green-500/20", text: "text-green-400", border: "border-green-500/40" },
  WET: { bg: "bg-blue-500/20", text: "text-blue-400", border: "border-blue-500/40" },
};

export function getTeamHex(teamNameOrHex: string): string {
  if (!teamNameOrHex) return "#EF4444";

  // Check if hex string (e.g. "3671C6" or "#3671C6")
  if (/^[0-9A-Fa-f]{6}$/.test(teamNameOrHex)) {
    return `#${teamNameOrHex}`;
  }
  if (teamNameOrHex.startsWith("#")) {
    return teamNameOrHex;
  }

  // Lookup in TEAM_COLORS dictionary
  return TEAM_COLORS[teamNameOrHex]?.hex ?? "#EF4444";
}

