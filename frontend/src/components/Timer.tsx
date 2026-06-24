"use client";

import { useEffect, useState } from "react";

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

export function Timer() {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, []);

  return (
    <span className="tag" aria-label="경과 시간">
      ⏱ {pad(Math.floor(seconds / 60))}:{pad(seconds % 60)}
    </span>
  );
}
