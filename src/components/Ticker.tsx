const items = [
  "Cross-Dimensional Contradiction Detection",
  "Trust Score with Confidence Level",
  "Actionable Recommendations",
  "AI-Powered Plain-Language Explanations",
  "Financial Encumbrance Check",
  "Odometer Integrity Analysis",
  "Ownership Chain Verification",
  "Accident & Insurance History",
  "Service Record Audit",
];

export default function Ticker() {
  const doubled = [...items, ...items];
  return (
    <div className="bg-orange-500/10 border-y border-orange-500/20 py-3 overflow-hidden">
      <div className="ticker-track">
        {doubled.map((item, i) => (
          <span key={i} className="flex items-center gap-4 px-6 text-sm text-orange-300 whitespace-nowrap">
            <span className="text-orange-500">◆</span>
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}
