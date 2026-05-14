"use client";

import { useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

interface ServiceEntry {
  date: string;
  odometer: string;
  items: string;
  workshop: string;
}

interface InsuranceClaim {
  year: string;
  amount: string;
  description: string;
}

interface FormData {
  make: string;
  model: string;
  year: string;
  registration: string;
  listing_price: string;
  odometer_reading: string;
  rc_owner_name: string;
  rc_registration_date: string;
  rc_owner_count: string;
  hypothecation_bank: string;
  service_entries: ServiceEntry[];
  insurance_claims: InsuranceClaim[];
  seller_claims_clean_history: boolean;
  seller_claims_single_owner: boolean;
  seller_loan_disclosure: string;
}

interface TrustReport {
  verdict: string;
  composite_score: number;
  confidence_level: string;
  verdict_explanation: string;
  assessments: Array<{
    dimension: string;
    state: string;
    score: number;
    summary: string;
    flags: Array<{ flag_id: string; severity: string; description: string }>;
  }>;
  action_checklist: string[];
  cost_estimate?: {
    total_low: number;
    total_high: number;
    currency: string;
  };
  contradictions: Array<{
    contradiction_id: string;
    severity: string;
    description: string;
  }>;
}

const VERDICT_STYLE: Record<string, { label: string; bg: string; text: string; border: string }> = {
  BUY: { label: "GO AHEAD — BUY", bg: "bg-green-500/15", text: "text-green-400", border: "border-green-500/40" },
  NEGOTIATE: { label: "NEGOTIATE", bg: "bg-yellow-500/15", text: "text-yellow-400", border: "border-yellow-500/40" },
  NEGOTIATE_WITH_SAFEGUARDS: { label: "NEGOTIATE WITH SAFEGUARDS", bg: "bg-orange-500/15", text: "text-orange-400", border: "border-orange-500/40" },
  WALK_AWAY: { label: "DO NOT BUY — WALK AWAY", bg: "bg-red-500/15", text: "text-red-400", border: "border-red-500/40" },
};

const STATE_LABELS: Record<string, string> = {
  verified_clean: "Clean",
  verified_flagged: "Flagged",
  unverifiable: "Unverifiable",
  active_resolvable: "Resolvable",
  critical: "Critical",
};

const SEV_COLOR: Record<string, string> = {
  critical: "bg-red-500/20 text-red-300",
  high: "bg-orange-500/20 text-orange-300",
  medium: "bg-yellow-500/20 text-yellow-300",
  low: "bg-blue-500/20 text-blue-300",
};

const emptyService = (): ServiceEntry => ({ date: "", odometer: "", items: "", workshop: "" });
const emptyClaim = (): InsuranceClaim => ({ year: "", amount: "", description: "" });

export default function AssessPage() {
  const [form, setForm] = useState<FormData>({
    make: "",
    model: "",
    year: "",
    registration: "",
    listing_price: "",
    odometer_reading: "",
    rc_owner_name: "",
    rc_registration_date: "",
    rc_owner_count: "1",
    hypothecation_bank: "",
    service_entries: [emptyService()],
    insurance_claims: [],
    seller_claims_clean_history: false,
    seller_claims_single_owner: false,
    seller_loan_disclosure: "not_mentioned",
  });

  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<TrustReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  function setField<K extends keyof FormData>(key: K, value: FormData[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function updateService(i: number, field: keyof ServiceEntry, val: string) {
    const entries = [...form.service_entries];
    entries[i] = { ...entries[i], [field]: val };
    setField("service_entries", entries);
  }

  function updateClaim(i: number, field: keyof InsuranceClaim, val: string) {
    const claims = [...form.insurance_claims];
    claims[i] = { ...claims[i], [field]: val };
    setField("insurance_claims", claims);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setReport(null);

    try {
      const res = await fetch("/api/assess", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: "Assessment failed" }));
        throw new Error(err.error || "Assessment failed");
      }
      const data = await res.json();
      setReport(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  function handleReset() {
    setReport(null);
    setError(null);
  }

  const verdictStyle = report ? (VERDICT_STYLE[report.verdict] ?? VERDICT_STYLE.NEGOTIATE) : null;

  return (
    <>
      <Navbar />
      <main className="min-h-screen pt-20 pb-16">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">
          {!report ? (
            <>
              <div className="text-center mb-10 pt-8">
                <h1 className="text-3xl sm:text-4xl font-bold text-white mb-3">
                  Assess a Car
                </h1>
                <p className="text-slate-400">
                  Fill in the details below. The more data you provide, the more
                  accurate the assessment.
                </p>
              </div>

              <form onSubmit={handleSubmit} className="flex flex-col gap-6">
                {/* Vehicle basics */}
                <Section title="Vehicle Details">
                  <div className="grid sm:grid-cols-2 gap-4">
                    <Field label="Make *" required>
                      <input
                        required
                        placeholder="e.g. Maruti Suzuki"
                        value={form.make}
                        onChange={(e) => setField("make", e.target.value)}
                      />
                    </Field>
                    <Field label="Model *" required>
                      <input
                        required
                        placeholder="e.g. Swift VXI"
                        value={form.model}
                        onChange={(e) => setField("model", e.target.value)}
                      />
                    </Field>
                    <Field label="Year *" required>
                      <input
                        required
                        type="number"
                        min="1990"
                        max={new Date().getFullYear()}
                        placeholder="e.g. 2019"
                        value={form.year}
                        onChange={(e) => setField("year", e.target.value)}
                      />
                    </Field>
                    <Field label="Registration Number">
                      <input
                        placeholder="e.g. MH02AB1234"
                        value={form.registration}
                        onChange={(e) => setField("registration", e.target.value.toUpperCase())}
                      />
                    </Field>
                    <Field label="Asking Price (Rs.)">
                      <input
                        type="number"
                        placeholder="e.g. 520000"
                        value={form.listing_price}
                        onChange={(e) => setField("listing_price", e.target.value)}
                      />
                    </Field>
                    <Field label="Odometer Reading (km)">
                      <input
                        type="number"
                        placeholder="e.g. 45000"
                        value={form.odometer_reading}
                        onChange={(e) => setField("odometer_reading", e.target.value)}
                      />
                    </Field>
                  </div>
                </Section>

                {/* RC Details */}
                <Section title="RC / Ownership Details">
                  <div className="grid sm:grid-cols-2 gap-4">
                    <Field label="RC Owner Name">
                      <input
                        placeholder="Name on RC document"
                        value={form.rc_owner_name}
                        onChange={(e) => setField("rc_owner_name", e.target.value)}
                      />
                    </Field>
                    <Field label="Registration Date">
                      <input
                        type="date"
                        value={form.rc_registration_date}
                        onChange={(e) => setField("rc_registration_date", e.target.value)}
                      />
                    </Field>
                    <Field label="Number of Previous Owners">
                      <input
                        type="number"
                        min="1"
                        max="10"
                        value={form.rc_owner_count}
                        onChange={(e) => setField("rc_owner_count", e.target.value)}
                      />
                    </Field>
                    <Field label="Hypothecation (Bank / NBFC)">
                      <input
                        placeholder="Leave blank if no loan"
                        value={form.hypothecation_bank}
                        onChange={(e) => setField("hypothecation_bank", e.target.value)}
                      />
                    </Field>
                  </div>
                </Section>

                {/* Service log */}
                <Section title="Service Log">
                  <p className="text-xs text-slate-500 mb-4">
                    Add entries from the service book. Leave blank items you
                    don&apos;t have.
                  </p>
                  {form.service_entries.map((entry, i) => (
                    <div key={i} className="grid sm:grid-cols-4 gap-3 mb-3">
                      <Field label="Date">
                        <input
                          type="month"
                          value={entry.date}
                          onChange={(e) => updateService(i, "date", e.target.value)}
                        />
                      </Field>
                      <Field label="Odometer (km)">
                        <input
                          type="number"
                          placeholder="km at service"
                          value={entry.odometer}
                          onChange={(e) => updateService(i, "odometer", e.target.value)}
                        />
                      </Field>
                      <Field label="Work Done">
                        <input
                          placeholder="oil change, brakes..."
                          value={entry.items}
                          onChange={(e) => updateService(i, "items", e.target.value)}
                        />
                      </Field>
                      <Field label="Workshop">
                        <input
                          placeholder="ASC / local"
                          value={entry.workshop}
                          onChange={(e) => updateService(i, "workshop", e.target.value)}
                        />
                      </Field>
                    </div>
                  ))}
                  <div className="flex gap-3 mt-1">
                    <button
                      type="button"
                      onClick={() => setField("service_entries", [...form.service_entries, emptyService()])}
                      className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      + Add row
                    </button>
                    {form.service_entries.length > 1 && (
                      <button
                        type="button"
                        onClick={() => setField("service_entries", form.service_entries.slice(0, -1))}
                        className="text-xs text-red-400 hover:text-red-300 transition-colors"
                      >
                        Remove last
                      </button>
                    )}
                  </div>
                </Section>

                {/* Insurance */}
                <Section title="Insurance Claims (if any)">
                  <p className="text-xs text-slate-500 mb-4">
                    Add known insurance claims. Leave this section blank if none.
                  </p>
                  {form.insurance_claims.map((claim, i) => (
                    <div key={i} className="grid sm:grid-cols-3 gap-3 mb-3">
                      <Field label="Year">
                        <input
                          type="number"
                          min="2000"
                          max={new Date().getFullYear()}
                          placeholder="Year of claim"
                          value={claim.year}
                          onChange={(e) => updateClaim(i, "year", e.target.value)}
                        />
                      </Field>
                      <Field label="Claim Amount (Rs.)">
                        <input
                          type="number"
                          placeholder="e.g. 45000"
                          value={claim.amount}
                          onChange={(e) => updateClaim(i, "amount", e.target.value)}
                        />
                      </Field>
                      <Field label="Description">
                        <input
                          placeholder="rear dent, flood, etc."
                          value={claim.description}
                          onChange={(e) => updateClaim(i, "description", e.target.value)}
                        />
                      </Field>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => setField("insurance_claims", [...form.insurance_claims, emptyClaim()])}
                    className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    + Add claim
                  </button>
                </Section>

                {/* Seller claims */}
                <Section title="Seller Disclosures">
                  <div className="flex flex-col gap-3">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={form.seller_claims_clean_history}
                        onChange={(e) => setField("seller_claims_clean_history", e.target.checked)}
                        className="w-4 h-4 accent-orange-500"
                      />
                      <span className="text-sm text-slate-300">
                        Seller claims clean accident history
                      </span>
                    </label>
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={form.seller_claims_single_owner}
                        onChange={(e) => setField("seller_claims_single_owner", e.target.checked)}
                        className="w-4 h-4 accent-orange-500"
                      />
                      <span className="text-sm text-slate-300">
                        Seller claims single owner
                      </span>
                    </label>
                    <Field label="Loan Disclosure by Seller">
                      <select
                        value={form.seller_loan_disclosure}
                        onChange={(e) => setField("seller_loan_disclosure", e.target.value)}
                      >
                        <option value="not_mentioned">Not mentioned</option>
                        <option value="denied">Seller denied any loan</option>
                        <option value="acknowledged">Seller acknowledged loan</option>
                        <option value="closure_plan">Seller provided closure plan</option>
                      </select>
                    </Field>
                  </div>
                </Section>

                {error && (
                  <div className="bg-red-500/15 border border-red-500/30 rounded-xl p-4 text-sm text-red-300">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-4 bg-orange-500 hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-full text-lg transition-all"
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24" fill="none">
                        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeOpacity="0.3" />
                        <path d="M12 2a10 10 0 0 1 10 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                      </svg>
                      Analysing...
                    </span>
                  ) : (
                    "Generate Trust Report →"
                  )}
                </button>
              </form>
            </>
          ) : (
            <div className="pt-8">
              {/* Verdict banner */}
              <div className={`rounded-2xl border ${verdictStyle!.border} ${verdictStyle!.bg} p-6 mb-8 text-center`}>
                <div className="text-xs text-slate-400 mb-1">Trust Verdict</div>
                <div className={`text-3xl sm:text-4xl font-black ${verdictStyle!.text} mb-2`}>
                  {verdictStyle!.label}
                </div>
                <div className="text-sm text-slate-300 max-w-xl mx-auto">
                  {report.verdict_explanation}
                </div>
                <div className="flex items-center justify-center gap-8 mt-5">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-white">
                      {Math.round(report.composite_score * 100)}
                    </div>
                    <div className="text-xs text-slate-400">Trust Score</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-white capitalize">
                      {report.confidence_level}
                    </div>
                    <div className="text-xs text-slate-400">Confidence</div>
                  </div>
                </div>
              </div>

              {/* Dimensions */}
              <h2 className="text-lg font-semibold text-white mb-4">Dimension Breakdown</h2>
              <div className="flex flex-col gap-3 mb-8">
                {report.assessments.map((a) => (
                  <details
                    key={a.dimension}
                    className="bg-[#0f1c35] border border-white/8 rounded-xl overflow-hidden"
                  >
                    <summary className="flex items-center gap-3 px-5 py-4 cursor-pointer list-none">
                      <span
                        className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                          a.state === "verified_clean"
                            ? "bg-green-500"
                            : a.state === "critical"
                            ? "bg-red-500"
                            : a.state === "unverifiable"
                            ? "bg-slate-500"
                            : "bg-yellow-500"
                        }`}
                      />
                      <span className="font-medium text-white capitalize flex-1">
                        {a.dimension.replace(/_/g, " ")}
                      </span>
                      <span className="text-xs text-slate-400 px-2 py-0.5 bg-white/8 rounded-full">
                        {STATE_LABELS[a.state] ?? a.state}
                      </span>
                      <span className="text-sm font-semibold text-white w-8 text-right">
                        {Math.round(a.score)}
                      </span>
                    </summary>
                    <div className="px-5 pb-4 pt-2 border-t border-white/5">
                      <p className="text-sm text-slate-400 mb-3">{a.summary}</p>
                      {a.flags.map((f) => (
                        <div
                          key={f.flag_id}
                          className="mb-2 flex items-start gap-2"
                        >
                          <span className={`flex-shrink-0 text-xs px-2 py-0.5 rounded-full ${SEV_COLOR[f.severity] ?? SEV_COLOR.low}`}>
                            {f.severity}
                          </span>
                          <span className="text-sm text-slate-300">
                            {f.description}
                          </span>
                        </div>
                      ))}
                    </div>
                  </details>
                ))}
              </div>

              {/* Contradictions */}
              {report.contradictions.length > 0 && (
                <div className="mb-8">
                  <h2 className="text-lg font-semibold text-white mb-4">
                    Contradictions Detected
                  </h2>
                  {report.contradictions.map((c) => (
                    <div
                      key={c.contradiction_id}
                      className="bg-red-500/10 border border-red-500/25 rounded-xl p-4 mb-3 text-sm text-slate-300"
                    >
                      <span className="text-xs font-semibold text-red-400 uppercase mr-2">
                        {c.severity}
                      </span>
                      {c.description}
                    </div>
                  ))}
                </div>
              )}

              {/* Action checklist */}
              {report.action_checklist.length > 0 && (
                <div className="mb-8">
                  <h2 className="text-lg font-semibold text-white mb-4">
                    Action Checklist
                  </h2>
                  <div className="bg-[#0f1c35] border border-white/8 rounded-xl p-5">
                    <ul className="flex flex-col gap-2">
                      {report.action_checklist.map((item, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm text-slate-300">
                          <span className="text-orange-500 mt-0.5 flex-shrink-0">→</span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Cost estimate */}
              {report.cost_estimate && (
                <div className="mb-8 bg-[#0f1c35] border border-white/8 rounded-xl p-5">
                  <h2 className="text-base font-semibold text-white mb-1">
                    Estimated Repair / Maintenance Cost
                  </h2>
                  <div className="text-2xl font-bold text-orange-400">
                    Rs. {report.cost_estimate.total_low.toLocaleString("en-IN")} –{" "}
                    {report.cost_estimate.total_high.toLocaleString("en-IN")}
                  </div>
                </div>
              )}

              <button
                onClick={handleReset}
                className="w-full py-3.5 border border-white/20 hover:border-white/40 text-white font-semibold rounded-full transition-colors text-sm"
              >
                ← Assess Another Car
              </button>
            </div>
          )}
        </div>
      </main>
      <Footer />
    </>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-[#0f1c35] border border-white/8 rounded-2xl p-6">
      <h2 className="text-base font-semibold text-white mb-5">{title}</h2>
      {children}
    </div>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactElement;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs text-slate-400">
        {label}
        {required && <span className="text-orange-400 ml-0.5">*</span>}
      </label>
      {/* Clone child and inject className */}
      {children
        ? (() => {
            const child = children as React.ReactElement<React.InputHTMLAttributes<HTMLInputElement> & React.SelectHTMLAttributes<HTMLSelectElement>>;
            const tag = child.type;
            const isSelect = tag === "select";
            const baseClass =
              "w-full bg-[#070d1a] border border-white/12 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-orange-500/50";
            const selectClass = `${baseClass} appearance-none`;
            return (
              <child.type
                {...child.props}
                className={isSelect ? selectClass : baseClass}
              />
            );
          })()
        : null}
    </div>
  );
}
