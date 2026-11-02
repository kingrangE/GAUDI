"use client";

import { useEffect, useRef, useState } from "react";

function format(total: number): string {
  const minutes = Math.floor(total / 60)
    .toString()
    .padStart(2, "0");
  const seconds = (total % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

/** The server enforces deadlines; the callback stops new input in exam screens. */
export function CountdownTimer({ seconds, onExpire }: { seconds: number; onExpire?: () => void }) {
  const [remaining, setRemaining] = useState(seconds);
  const callback = useRef(onExpire);
  callback.current = onExpire;

  useEffect(() => {
    const deadline = Date.now() + seconds * 1000;
    const id = setInterval(() => {
      const left = Math.max(0, Math.ceil((deadline - Date.now()) / 1000));
      setRemaining(left);
      if (left === 0) {
        clearInterval(id);
        callback.current?.();
      }
    }, 250);
    setRemaining(seconds);
    return () => clearInterval(id);
  }, [seconds]);

  return (
    <span className="font-mono text-sm text-ink-soft" aria-label="남은 시간">
      {format(remaining)}
    </span>
  );
}
