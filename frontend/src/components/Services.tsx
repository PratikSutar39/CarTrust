const services = [
  {
    icon: "🔑",
    title: "Ownership Verification",
    description:
      "We trace the complete ownership chain — number of previous owners, transfer gaps, hypothecation status, and RC authenticity.",
    color: "from-blue-500/20 to-blue-600/10",
    border: "border-blue-500/20",
    badge: "bg-blue-500/20 text-blue-300",
  },
  {
    icon: "📏",
    title: "Odometer Integrity",
    description:
      "Cross-references stated mileage with service records and age-adjusted norms. Detects rollbacks, implausible readings, and inconsistencies.",
    color: "from-purple-500/20 to-purple-600/10",
    border: "border-purple-500/20",
    badge: "bg-purple-500/20 text-purple-300",
  },
  {
    icon: "🚗",
    title: "Accident History",
    description:
      "Analyses insurance claim history, undisclosed repairs, airbag deployments, and structural damage indicators from multiple sources.",
    color: "from-red-500/20 to-red-600/10",
    border: "border-red-500/20",
    badge: "bg-red-500/20 text-red-300",
  },
  {
    icon: "💰",
    title: "Financial Encumbrance",
    description:
      "Checks for active loans, hypothecation liens, and undisclosed financial liabilities that could prevent clean title transfer.",
    color: "from-yellow-500/20 to-yellow-600/10",
    border: "border-yellow-500/20",
    badge: "bg-yellow-500/20 text-yellow-300",
  },
  {
    icon: "🔧",
    title: "Service History & Cost",
    description:
      "Reviews service log completeness, gap analysis, major repair patterns, and estimates upcoming maintenance costs for your budget.",
    color: "from-green-500/20 to-green-600/10",
    border: "border-green-500/20",
    badge: "bg-green-500/20 text-green-300",
  },
];

export default function Services() {
  return (
    <section id="services" className="py-24 bg-[#070d1a]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        {/* Header */}
        <div className="text-center mb-14">
          <span className="inline-block px-3 py-1 bg-orange-500/10 border border-orange-500/30 rounded-full text-orange-400 text-xs font-medium mb-4">
            What We Analyse
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            Comprehensive Trust Assessment
          </h2>
          <p className="text-slate-400 max-w-2xl mx-auto text-lg">
            Every used car is assessed across five critical dimensions before
            you commit a single rupee.
          </p>
        </div>

        {/* Cards grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {services.map((s) => (
            <div
              key={s.title}
              className={`relative group rounded-2xl border ${s.border} bg-gradient-to-br ${s.color} p-6 hover:scale-[1.02] transition-transform`}
            >
              <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl ${s.badge} text-2xl mb-4`}>
                {s.icon}
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">{s.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{s.description}</p>
            </div>
          ))}

          {/* Bonus card */}
          <div className="relative rounded-2xl border border-orange-500/30 bg-gradient-to-br from-orange-500/15 to-orange-600/5 p-6 flex flex-col justify-between hover:scale-[1.02] transition-transform">
            <div>
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-orange-500/20 text-2xl mb-4">
                ⚡
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">
                Contradiction Detection
              </h3>
              <p className="text-slate-400 text-sm leading-relaxed">
                Our AI cross-checks all five dimensions for conflicts — like
                high mileage claims contradicting a minimal service log.
              </p>
            </div>
            <div className="mt-4 text-xs text-orange-400 font-medium">
              Included in every report →
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
