import type { Metadata } from "next";
import "./globals.css";
import AppShellWrapper from "@/components/layout/AppShellWrapper";

export const metadata: Metadata = {
  title: "Ghost Operators NIDS",
  description: "Advanced Network Intrusion Detection & Prevention System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <AppShellWrapper>{children}</AppShellWrapper>
      </body>
    </html>
  );
}
