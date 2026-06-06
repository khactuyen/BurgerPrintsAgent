import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BurgerPrintsAgent | POD Assistant",
  description: "AI-powered fulfillment decision agent for BurgerPrints sellers",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
