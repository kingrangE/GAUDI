import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "and-you Admin",
  description: "Admin console for the and-you evaluation platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
