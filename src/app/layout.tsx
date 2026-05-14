import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CarTrust — Buy Used Cars with Confidence",
  description:
    "AI-powered trust assessment for used cars in India. Know before you buy.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${geistSans.variable} h-full`}>
      <body className="min-h-full bg-[#070d1a] text-white antialiased">
        {children}
      </body>
    </html>
  );
}
