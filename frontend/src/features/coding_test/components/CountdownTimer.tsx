"use client";

import { useEffect, useState } from "react";

function format(total: number): string {
  const minutes = Math.floor(total / 60)
    .toString()
    .padStart(2, "0");
  const seconds = (total % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

/** Display-only countdown — no enforcement, no auto-submit (MVP). */
export function CountdownTimer({ seconds }: { seconds: number }) {
  const [remaining, setRemaining] = useState(seconds);

  useEffect(() => {
    const id = setInterval(() => {
      setRemaining((r) => {
        if (r <= 1) {
          clearInterval(id);
          return 0;
        }
        return r - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <span className="font-mono text-sm text-slate-600" aria-label="남은 시간">
      {format(remaining)}
    </span>
  );
}
