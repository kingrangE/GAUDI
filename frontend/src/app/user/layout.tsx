"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import { getUserCode } from "@/lib/accessCodes";
import { ensureDemoSession, isDemoEnabled } from "@/features/demo/session";

/** Demo entry uses the server cookie; legacy entry keeps the local code gate. */
export default function UserLayout({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [allowed, setAllowed] = useState(false);

  useEffect(() => {
    if (isDemoEnabled()) {
      let active = true;
      ensureDemoSession().then(() => {
        if (active) setAllowed(true);
      }).catch(() => {
        if (active) router.replace("/");
      });
      return () => { active = false; };
    }
    if (getUserCode()) {
      setAllowed(true);
    } else {
      router.replace("/");
    }
  }, [router]);

  if (!allowed) return null;
  return <>{children}</>;
}
