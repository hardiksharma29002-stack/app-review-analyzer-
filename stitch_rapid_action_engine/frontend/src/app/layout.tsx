import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  weight: ["400", "700", "800"],
  variable: "--font-outfit",
});

export const metadata: Metadata = {
  title: "App Review Insights | Product Pulse",
  description: "Turn User Noise Into Product Strategy. An immersive AI-powered analytics dashboard.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={outfit.variable}>
      <body className="antialiased bg-background text-foreground overflow-x-hidden selection:bg-primary selection:text-background">
        {children}
      </body>
    </html>
  );
}
