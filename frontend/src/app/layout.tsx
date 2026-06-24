import type { ReactNode } from "react";

import "./globals.css";

export const metadata = {
  title: "and·you — 명세 설계",
  description: "AI Agent 활용 역량 평가 플랫폼",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
