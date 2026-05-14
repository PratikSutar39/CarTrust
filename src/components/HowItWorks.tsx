const steps = [
  {
    number: "01",
    title: "Enter Car Details",
    description:
      "Fill in the registration number, make, model, year, asking price, and odometer reading. Add RC details, service log, and insurance history.",
    icon: "📝",
  },
  {
    number: "02",
    title: "Rule Engine Runs",
    description:
      "Our deterministic rule engine processes every data point across all five trust dimensions — no hallucinations, no guesses.",
    icon: "⚙️",
  },
  {
    number: "03",
    title: "AI Explains",
    description:
      "The LLM reads the rule engine's output and writes plain-language explanations a first-time buyer can actually understand.",
    icon: "🤖",
  },
  {
    number: "04",
    title: "Get Your Verdict",
    description:
      "Receive a BUY / NEGOTIATE / WALK AWAY verdict with a trust score, action checklist, and estimated repair costs.",
    icon: "✅",
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-24 bg-[#0a1225]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-14">
          <span className="inline-block px-3 py-1 bg-blue-500/10 border border-blue-500/30 rounded-full text-blue-400 text-xs font-medium mb-4">
            The Process
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
            How It Works
          </h2>
          <p className="text-slate-400 max-w-xl mx-auto">
            From raw car data to a clear verdict in seconds — here&apos;s the
            three-layer process behind every CarTrust report.
          </p>
        </div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, i) => (
            <div key={step.number} className="relative">
              {/* Connector line */}
              {i < steps.length - 1 && (
                <div className="hidden lg:block absolute top-10 left-full w-full h-px bg-gradient-to-r from-white/20 to-transparent z-10" />
              )}

              <div className="bg-[#0f1c35] border border-white/8 rounded-2xl p-6 h-full">
                <div className="flex items-center gap-3 mb-4">
                  <span className="text-3xl">{step.icon}</span>
                  <span className="text-4xl font-black text-white/10 select-none">
                    {step.number}
                  </span>
                </div>
                <h3 className="text-base font-semibold text-white mb-2">
                  {step.title}
                </h3>
                <p className="text-sm text-slate-400 leading-relaxed">
                  {step.description}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Architecture callout */}
        <div className="mt-10 bg-[#0f1c35] border border-white/8 rounded-2xl p-6 flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-orange-500/20 flex items-center justify-center text-xl">
            🏗️
          </div>
          <div>
            <h4 className="font-semibold text-white mb-1">
              3-Layer Architecture
            </h4>
            <p className="text-sm text-slate-400">
              <span className="text-white">Extraction</span> (parse raw inputs) →{" "}
              <span className="text-white">Rule Engine</span> (deterministic logic) →{" "}
              <span className="text-white">LLM</span> (plain-language explanations only).
              The AI never decides the verdict — that&apos;s always rule-based.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
