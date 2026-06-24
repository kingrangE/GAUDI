import type { ReactNode } from "react";

export const metadata = {
  title: "and-you — 거부 능력 평가",
  description: "AI Agent 활용·검증 역량 평가 플랫폼",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ko">
      <body
        style={{
          fontFamily: "system-ui, sans-serif",
          maxWidth: 760,
          margin: "0 auto",
          padding: "24px 16px",
          lineHeight: 1.6,
        }}
      >
        {children}
      </body>
    </html>
  );
}
