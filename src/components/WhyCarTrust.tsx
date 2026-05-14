const reasons = [
  {
    icon: "🛡️",
    title: "Rule-Based Verdict — Always",
    description:
      "The BUY / NEGOTIATE / WALK AWAY decision is produced by deterministic rules, not AI guesses. The LLM only writes the explanation.",
  },
  {
    icon: "📊",
    title: "Evidence-Backed Flags",
    description:
      "Every flag is backed by specific evidence from the data you provide. No vague warnings — just specific, actionable findings.",
  },
  {
    icon: "🔗",
    title: "Cross-Dimensional Checks",
    description:
      "We detect contradictions between dimensions — e.g. very high mileage but almost no service records.",
  },
  {
    icon: "💡",
    title: "Plain Language for First-Time Buyers",
    description:
      "Complex findings are explained in simple language. No jargon. Written for someone buying their first car.",
  },
  {
    icon: "📄",
    title: "Downloadable PDF Report",
    description:
      "Every assessment generates a professional PDF report you can share, save, or use in negotiations.",
  },
  {
    icon: "🇮🇳",
    title: "Built for India",
    description:
      "Designed around Indian RC documents, RTO norms, rupee pricing, and the realities of India's used car market.",
  },
];

export default function WhyCarTrust() {
  return (
    <section id="why-cartrust" className="py-24 bg-[#070d1a]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <span className="inline-block px-3 py-1 bg-green-500/10 border border-green-500/30 rounded-full text-green-400 text-xs font-medium mb-4">
            Why Us
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Why CarTrust?
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            India&apos;s used car market is full of hidden surprises. CarTrust
            is built specifically to protect buyers from the most common traps.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {reasons.map((r) => (
            <div
              key={r.title}
              className="bg-[#0f1c35] border border-white/8 rounded-2xl p-6 hover:border-white/20 transition-colors"
            >
              <div className="text-3xl mb-3">{r.icon}</div>
              <h3 className="font-semibold text-white mb-2">{r.title}</h3>
              <p className="text-sm text-slate-400 leading-relaxed">
                {r.description}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
