import Link from "next/link";

const badges = [
  { icon: "🔍", label: "Multi-Source Verification" },
  { icon: "🤖", label: "AI + Rule Engine" },
  { icon: "📋", label: "Actionable Report" },
];

const trustStats = [
  { value: "5", label: "Trust Dimensions" },
  { value: "100%", label: "Rule-Based Logic" },
  { value: "AI", label: "LLM Explanations" },
  { value: "Free", label: "No Hidden Fees" },
];

export default function Hero() {
  return (
    <section className="relative min-h-screen flex items-center pt-16 overflow-hidden">
      {/* Background radial glows */}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-orange-500/8 rounded-full blur-3xl" />
        <div className="absolute top-1/3 right-1/4 w-[400px] h-[400px] bg-blue-600/8 rounded-full blur-3xl" />
        {/* Grid pattern */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,0.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.1) 1px, transparent 1px)",
            backgroundSize: "60px 60px",
          }}
        />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 w-full py-20">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* Left column */}
          <div className="flex flex-col gap-6">
            {/* Pill badge */}
            <div className="inline-flex w-fit items-center gap-2 px-3 py-1.5 bg-orange-500/10 border border-orange-500/30 rounded-full text-orange-400 text-xs font-medium">
              <span className="w-1.5 h-1.5 bg-orange-400 rounded-full animate-pulse" />
              India&apos;s First AI Used Car Trust Assessment
            </div>

            {/* Headline */}
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight">
              Buy Used Cars with{" "}
              <span className="text-orange-500">Confidence.</span>
              <br />
              Not Doubt.
            </h1>

            {/* Subtext */}
            <p className="text-slate-400 text-lg leading-relaxed max-w-lg">
              CarTrust analyses RC records, odometer history, insurance claims,
              loan encumbrances, and service logs — then gives you a clear{" "}
              <strong className="text-white">BUY / NEGOTIATE / WALK AWAY</strong>{" "}
              verdict powered by AI.
            </p>

            {/* Feature badges */}
            <div className="flex flex-wrap gap-3">
              {badges.map((b) => (
                <span
                  key={b.label}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-full text-blue-300 text-sm"
                >
                  <span>{b.icon}</span>
                  {b.label}
                </span>
              ))}
            </div>

            {/* CTA buttons */}
            <div className="flex flex-wrap gap-4 mt-2">
              <Link
                href="/assess"
                className="px-8 py-3.5 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-full transition-all hover:shadow-lg hover:shadow-orange-500/25 text-sm"
              >
                Assess a Car Now →
              </Link>
              <a
                href="#sample-reports"
                className="px-8 py-3.5 border border-white/20 hover:border-white/40 text-white font-semibold rounded-full transition-all hover:bg-white/5 text-sm"
              >
                View Sample Report
              </a>
            </div>

            {/* Trust stats */}
            <div className="flex flex-wrap gap-6 mt-4 pt-6 border-t border-white/10">
              {trustStats.map((s) => (
                <div key={s.label} className="flex flex-col">
                  <span className="text-xl font-bold text-orange-500">{s.value}</span>
                  <span className="text-xs text-slate-400">{s.label}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Right column — visual */}
          <div className="relative flex flex-col items-center gap-6">
            {/* Main card */}
            <div className="relative w-full max-w-sm bg-[#0f1c35] border border-white/10 rounded-2xl p-6 shadow-2xl">
              <div className="flex items-center justify-between mb-4">
                <span className="text-sm text-slate-400">Trust Assessment</span>
                <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-full">Live</span>
              </div>

              {/* Score ring */}
              <div className="flex items-center gap-4 mb-5">
                <div className="relative w-20 h-20 flex-shrink-0">
                  <svg viewBox="0 0 80 80" className="w-20 h-20 -rotate-90">
                    <circle cx="40" cy="40" r="32" fill="none" stroke="#1e3a5f" strokeWidth="8" />
                    <circle
                      cx="40"
                      cy="40"
                      r="32"
                      fill="none"
                      stroke="#f97316"
                      strokeWidth="8"
                      strokeDasharray="201"
                      strokeDashoffset="48"
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-lg font-bold text-white">76</span>
                  </div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-green-400">NEGOTIATE</div>
                  <div className="text-xs text-slate-400 mt-1">Confidence: High</div>
                  <div className="text-xs text-slate-400">2021 Maruti Swift</div>
                </div>
              </div>

              {/* Dimension list */}
              {[
                { name: "Ownership", state: "verified_clean", score: 90 },
                { name: "Odometer", state: "flagged", score: 62 },
                { name: "Accident", state: "verified_clean", score: 85 },
                { name: "Financial", state: "verified_clean", score: 95 },
                { name: "Service", state: "flagged", score: 55 },
              ].map((d) => (
                <div key={d.name} className="flex items-center gap-2 mb-2">
                  <span
                    className={`w-2 h-2 rounded-full flex-shrink-0 ${
                      d.state === "verified_clean" ? "bg-green-500" : "bg-yellow-500"
                    }`}
                  />
                  <span className="text-xs text-slate-300 flex-1">{d.name}</span>
                  <div className="w-20 h-1.5 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${
                        d.state === "verified_clean" ? "bg-green-500" : "bg-yellow-500"
                      }`}
                      style={{ width: `${d.score}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-400 w-6 text-right">{d.score}</span>
                </div>
              ))}
            </div>

            {/* Floating testimonial */}
            <div className="float-card w-full max-w-sm bg-[#0f1c35] border border-blue-500/20 rounded-xl p-4 shadow-lg shadow-blue-500/10">
              <div className="flex items-start gap-3">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-xs font-bold flex-shrink-0">
                  R
                </div>
                <div>
                  <div className="text-xs font-semibold text-white">Rahul M., Mumbai</div>
                  <p className="text-xs text-slate-400 mt-0.5 leading-relaxed">
                    "CarTrust saved me from a car with hidden loan dues and a
                    tampered odometer. The report was crystal clear."
                  </p>
                  <div className="flex mt-1.5 gap-0.5">
                    {Array.from({ length: 5 }).map((_, i) => (
                      <svg key={i} className="w-3 h-3 text-yellow-400 fill-current" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
