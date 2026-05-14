import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-[#050a15] border-t border-white/8 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="grid sm:grid-cols-3 gap-8 mb-10">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="text-orange-500">
                <svg width="24" height="24" viewBox="0 0 28 28" fill="none">
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
              <span className="font-bold text-white">
                Car<span className="text-orange-500">Trust</span>
              </span>
            </div>
            <p className="text-xs text-slate-500 leading-relaxed max-w-xs">
              AI-powered trust assessment for India&apos;s used car market.
              Know before you buy.
            </p>
          </div>

          {/* Links */}
          <div>
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
              Navigation
            </h4>
            <ul className="space-y-2">
              {[
                ["How It Works", "#how-it-works"],
                ["Our Services", "#services"],
                ["Why CarTrust", "#why-cartrust"],
                ["Sample Reports", "#sample-reports"],
                ["FAQ", "#faq"],
              ].map(([label, href]) => (
                <li key={label}>
                  <a
                    href={href}
                    className="text-sm text-slate-500 hover:text-slate-300 transition-colors"
                  >
                    {label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* CTA */}
          <div>
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
              Get Started
            </h4>
            <p className="text-sm text-slate-500 mb-4 leading-relaxed">
              Assess any used car in minutes. No registration required.
            </p>
            <Link
              href="/assess"
              className="inline-flex px-5 py-2.5 bg-orange-500 hover:bg-orange-600 text-white text-sm font-semibold rounded-full transition-colors"
            >
              Assess a Car →
            </Link>
          </div>
        </div>

        <div className="border-t border-white/8 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-600">
          <span>© {new Date().getFullYear()} CarTrust. Built for India&apos;s used car buyers.</span>
          <span>Powered by AI + Deterministic Rule Engine</span>
        </div>
      </div>
    </footer>
  );
}
