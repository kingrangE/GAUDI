// Difficulty presentation helpers — shared by the picker, problem brief and results.

export const DIFFICULTY_ORDER = ["easy", "medium", "hard"] as const;

const LABELS: Record<string, string> = {
  easy: "쉬움",
  medium: "보통",
  hard: "어려움",
};

export function difficultyLabel(difficulty: string): string {
  return LABELS[difficulty] ?? difficulty;
}

export function difficultyTone(difficulty: string): "good" | "warn" | "bad" | "neutral" {
  if (difficulty === "easy") return "good";
  if (difficulty === "medium") return "warn";
  if (difficulty === "hard") return "bad";
  return "neutral";
}
