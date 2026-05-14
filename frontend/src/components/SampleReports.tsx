import Link from "next/link";

const samples = [
  {
    car: "2019 Maruti Suzuki Swift VXI",
    price: "Rs. 5,20,000",
    verdict: "BUY",
    score: 84,
    verdictColor: "text-green-400",
    verdictBg: "bg-green-500/15 border-green-500/30",
    summary: "Clean ownership, consistent odometer, no active loans. Minor service gap noted but non-critical.",
    flags: ["Minor service gap (4 months)"],
    dimensions: [
      { name: "Ownership", score: 92, ok: true },
      { name: "Odometer", score: 88, ok: true },
      { name: "Accident", score: 90, ok: true },
      { name: "Financial", score: 95, ok: true },
      { name: "Service", score: 72, ok: true },
    ],
  },
  {
    car: "2017 Honda City ZX CVT",
    price: "Rs. 7,85,000",
    verdict: "NEGOTIATE",
    score: 67,
    verdictColor: "text-yellow-400",
    verdictBg: "bg-yellow-500/15 border-yellow-500/30",
    summary: "Odometer reading 18% higher than service records imply. Seller claims checked — inconsistencies found.",
    flags: ["Odometer discrepancy (18%)", "Undisclosed minor accident"],
    dimensions: [
      { name: "Ownership", score: 88, ok: true },
      { name: "Odometer", score: 45, ok: false },
      { name: "Accident", score: 60, ok: false },
      { name: "Financial", score: 90, ok: true },
      { name: "Service", score: 78, ok: true },
    ],
  },
  {
    car: "2020 Hyundai Creta SX 4WD",
    price: "Rs. 13,50,000",
    verdict: "WALK AWAY",
    score: 0,
    verdictColor: "text-red-400",
    verdictBg: "bg-red-500/15 border-red-500/30",
    summary: "Active bank loan on RC. Seller denied loan existence. Hard stop triggered — ownership transfer legally blocked.",
    flags: ["Active hypothecation loan", "Seller misrepresentation"],
    dimensions: [
      { name: "Ownership", score: 70, ok: true },
      { name: "Odometer", score: 80, ok: true },
      { name: "Accident", score: 75, ok: true },
      { name: "Financial", score: 0, ok: false },
      { name: "Service", score: 82, ok: true },
    ],
  },
];

export default function SampleReports() {
  return (
    <section id="sample-reports" className="py-24 bg-[#0a1225]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <span className="inline-block px-3 py-1 bg-purple-500/10 border border-purple-500/30 rounded-full text-purple-400 text-xs font-medium mb-4">
            Sample Reports
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            See What a Report Looks Like
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            Three real-world scenarios — a clean car, a negotiation candidate,
            and a hard stop.
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-6">
          {samples.map((s) => (
            <div
              key={s.car}
              className={`rounded-2xl border ${s.verdictBg} p-6 flex flex-col gap-4`}
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h3 className="font-semibold text-white text-sm">{s.car}</h3>
                  <p className="text-xs text-slate-400 mt-0.5">Asking: {s.price}</p>
                </div>
                <div className="text-right flex-shrink-0">
                  <div className={`font-black text-lg ${s.verdictColor}`}>
                    {s.verdict}
                  </div>
                  {s.score > 0 && (
                    <div className="text-xs text-slate-400">Score: {s.score}/100</div>
                  )}
                </div>
              </div>

              {/* Summary */}
              <p className="text-xs text-slate-300 leading-relaxed">{s.summary}</p>

              {/* Flags */}
              {s.flags.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {s.flags.map((f) => (
                    <span
                      key={f}
                      className="text-xs px-2 py-0.5 bg-white/8 rounded-full text-slate-300"
                    >
                      ⚠ {f}
                    </span>
                  ))}
                </div>
              )}

              {/* Dimension bars */}
              <div className="space-y-1.5">
                {s.dimensions.map((d) => (
                  <div key={d.name} className="flex items-center gap-2">
                    <span
                      className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${d.ok ? "bg-green-500" : "bg-red-500"}`}
                    />
                    <span className="text-xs text-slate-400 w-16">{d.name}</span>
                    <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${d.ok ? "bg-green-500" : "bg-red-500"}`}
                        style={{ width: `${d.score}%` }}
                      />
                    </div>
                    <span className="text-xs text-slate-500 w-6 text-right">{d.score}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-10 text-center">
          <Link
            href="/assess"
            className="inline-flex items-center gap-2 px-8 py-3.5 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-full transition-all text-sm"
          >
            Assess Your Car Now →
          </Link>
        </div>
      </div>
    </section>
  );
}
