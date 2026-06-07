import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Sidebar from "../component/Sidebar";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Startup Radar - Market Intelligence Platform",
  description: "AI-powered SaaS tool tracking emerging AI niches, repositories, and startup opportunities.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
      suppressHydrationWarning={true}
    >
      <body className="min-h-full flex text-zinc-100 bg-zinc-950 font-sans" suppressHydrationWarning={true}>
        {/* Sidebar Component */}
        <Sidebar />
        
        {/* Main Application Area */}
        <div className="flex-1 flex flex-col h-screen overflow-y-auto">
          {children}
        </div>
      </body>
    </html>
  );
}
