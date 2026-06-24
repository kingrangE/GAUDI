"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import { getUserCode } from "@/lib/accessCodes";

/**
 * Light entry guard: the user area is reachable only after a user code was
 * entered at the gate. Without one (e.g. a direct URL hit), bounce back to `/`.
 * This is access separation, not authentication — login lands later.
 */
export default function UserLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    if (getUserCode()) {
      setAllowed(true);
    } else {
      router.replace("/");
    }
  }, [router]);

  if (!allowed) return null;
  return <>{children}</>;
}
