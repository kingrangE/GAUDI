import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";
import { AppShell } from "@/components/ui/AppShell";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "and-you — AI Agent 역량 평가",
  description: "AI Agent 활용·검증 역량 평가 플랫폼",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-paper text-ink-900">
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
