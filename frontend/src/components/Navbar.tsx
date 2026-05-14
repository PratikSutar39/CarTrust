"use client";

import Link from "next/link";
import { useState } from "react";

const navLinks = [
  { label: "About", href: "#about" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Our Services", href: "#services" },
  { label: "Why CarTrust", href: "#why-cartrust" },
  { label: "Sample Reports", href: "#sample-reports" },
  { label: "FAQ", href: "#faq" },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-[#070d1a]/90 backdrop-blur-md border-b border-white/10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-16">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <span className="text-orange-500">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <path
                d="M14 2L4 8v8c0 5.25 4.27 10.16 10 11.33C19.73 26.16 24 21.25 24 16V8L14 2z"
                fill="#f97316"
                fillOpacity="0.2"
                stroke="#f97316"
                strokeWidth="1.5"
              />
              <path
                d="M10 14l3 3 5-5"
                stroke="#f97316"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </span>
          <span className="font-bold text-xl text-white">
            Car<span className="text-orange-500">Trust</span>
          </span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden lg:flex items-center gap-6">
          {navLinks.map((l) => (
            <a
              key={l.href}
              href={l.href}
              className="text-sm text-slate-300 hover:text-white transition-colors"
            >
              {l.label}
            </a>
          ))}
        </div>

        {/* CTA */}
        <div className="hidden lg:flex">
          <Link
            href="/assess"
            className="px-5 py-2 bg-orange-500 hover:bg-orange-600 text-white text-sm font-semibold rounded-full transition-colors"
          >
            Get Started
          </Link>
        </div>

        {/* Hamburger */}
        <button
          className="lg:hidden text-white p-2"
          onClick={() => setOpen(!open)}
          aria-label="Toggle menu"
        >
          <svg width="22" height="22" fill="none" stroke="currentColor" strokeWidth="2">
            {open ? (
              <>
                <line x1="4" y1="4" x2="18" y2="18" />
                <line x1="18" y1="4" x2="4" y2="18" />
              </>
            ) : (
              <>
                <line x1="3" y1="7" x2="19" y2="7" />
                <line x1="3" y1="12" x2="19" y2="12" />
                <line x1="3" y1="17" x2="19" y2="17" />
              </>
            )}
          </svg>
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="lg:hidden border-t border-white/10 bg-[#0a1225] px-4 py-4 flex flex-col gap-3">
          {navLinks.map((l) => (
            <a
              key={l.href}
              href={l.href}
              onClick={() => setOpen(false)}
              className="text-sm text-slate-300 hover:text-white py-1"
            >
              {l.label}
            </a>
          ))}
          <Link
            href="/assess"
            className="mt-2 px-5 py-2 bg-orange-500 text-white text-sm font-semibold rounded-full text-center"
            onClick={() => setOpen(false)}
          >
            Get Started
          </Link>
        </div>
      )}
    </nav>
  );
}
