"use client";

import { useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

// ── Car database (Make → Model → Variants) ───────────────────────────────────
const CAR_DATABASE: Record<string, Record<string, string[]>> = {
  "Maruti Suzuki": {
    "Alto": ["LXi", "VXi", "VXi+"],
    "Alto K10": ["STD", "VXi", "VXi+", "VXi AGS", "ZXi", "ZXi+"],
    "S-Presso": ["STD", "LXi", "VXi", "VXi+", "VXi+ AMT"],
    "Celerio": ["LXi", "VXi", "ZXi", "ZXi+", "ZXi AMT"],
    "WagonR": ["LXi 1.0", "LXi 1.2", "VXi 1.0", "VXi 1.2", "ZXi 1.2", "ZXi+ 1.2", "ZXi AMT"],
    "Swift": ["LXi", "VXi", "ZXi", "ZXi+", "VXi AMT", "ZXi AMT", "ZXi+ AMT"],
    "Baleno": ["Sigma", "Delta", "Zeta", "Alpha", "Delta AMT", "Zeta AMT"],
    "Ignis": ["Sigma", "Delta", "Zeta", "Alpha", "Delta AMT", "Zeta AMT"],
    "Dzire": ["LXi", "VXi", "ZXi", "ZXi+", "VXi AMT", "ZXi AMT"],
    "Ciaz": ["Sigma", "Delta", "Zeta", "Alpha", "Smart Hybrid Delta", "Smart Hybrid Alpha"],
    "Ertiga": ["LXi", "VXi", "ZXi", "ZXi+", "VXi CNG", "ZXi CNG"],
    "XL6": ["Zeta", "Alpha", "Zeta Plus", "Alpha Plus"],
    "Brezza": ["LXi", "VXi", "ZXi", "ZXi+", "VXi AMT", "ZXi AMT", "ZXi+ AMT"],
    "Grand Vitara": ["Sigma", "Delta", "Zeta", "Alpha", "Zeta+", "Alpha+", "AllGrip Pro"],
    "Fronx": ["Sigma", "Delta", "Zeta", "Alpha", "Zeta Turbo", "Alpha Turbo"],
    "Jimny": ["Zeta 3-Door", "Alpha 3-Door", "Zeta 5-Door", "Alpha 5-Door"],
  },
  "Hyundai": {
    "i10": ["Era", "Magna", "Sportz", "Asta"],
    "Grand i10": ["Era", "Magna", "Sportz", "Asta", "Asta (O)"],
    "Grand i10 Nios": ["Era", "Magna", "Sportz", "Asta", "Asta (O)", "Sportz AMT", "Asta AMT"],
    "i20": ["Era", "Magna", "Sportz", "Asta", "Asta (O)", "N Line N6", "N Line N8"],
    "Aura": ["E", "S", "S CNG", "SX", "SX+", "SX AMT"],
    "Verna": ["EX", "S", "SX", "SX (O)", "SX+ Turbo", "SX (O) Turbo"],
    "City": ["V", "VX", "ZX", "VX MT", "ZX MT"],
    "Creta": ["E", "EX", "S", "S (O)", "SX", "SX (O)", "SX Tech"],
    "Venue": ["E", "S", "S+", "SX", "SX (O)", "N Line N6", "N Line N8"],
    "Alcazar": ["Prestige", "Prestige (O)", "Platinum", "Signature", "Signature (O)"],
    "Exter": ["EX", "S", "S (O)", "SX", "SX (O)", "S AMT"],
    "Tucson": ["Platinum", "Signature FWD", "Signature AWD"],
  },
  "Tata": {
    "Nano": ["STD", "CX", "LX", "XE", "XM", "XT"],
    "Tiago": ["XE", "XM", "XT", "XZ", "XZ+", "XZA", "XZA+"],
    "Tigor": ["XE", "XM", "XMA", "XT", "XTA", "XZ+", "XZA+"],
    "Altroz": ["XE", "XM", "XM+", "XT", "XZ", "XZ+", "XZA", "XZA+"],
    "Punch": ["Pure", "Adventure", "Accomplished", "Creative", "Creative AMT", "Accomplished AMT"],
    "Nexon": ["Smart", "Smart+", "Pure", "Creative", "Fearless", "Fearless+", "Creative AMT", "Fearless AMT"],
    "Harrier": ["Smart", "Smart+", "Pure", "Adventure", "Accomplished", "Creative", "Creative AMT"],
    "Safari": ["Smart", "Smart+", "Pure", "Adventure", "Accomplished", "Creative", "Gold"],
    "Curvv": ["Smart", "Smart+", "Creative", "Accomplished", "Creative AMT"],
  },
  "Honda": {
    "Brio": ["S MT", "S AT", "V MT", "V AT", "VX MT", "VX AT"],
    "Jazz": ["S", "SV", "V", "VX", "V CVT", "VX CVT"],
    "Amaze": ["E MT", "S MT", "V MT", "VX MT", "S CVT", "V CVT", "VX CVT"],
    "City": ["V MT", "VX MT", "ZX MT", "V CVT", "VX CVT", "ZX CVT", "Hybrid"],
    "WR-V": ["S", "SV", "V", "VX"],
    "Elevate": ["SV MT", "V MT", "VX MT", "ZX MT", "S CVT", "V CVT", "VX CVT", "ZX CVT"],
  },
  "Kia": {
    "Seltos": ["HTE", "HTK", "HTK+", "HTX", "HTX+", "GTX+", "X-Line"],
    "Sonet": ["HTE", "HTK", "HTK+", "HTX", "HTX+", "GTX+", "X-Line"],
    "Carens": ["Premium", "Prestige", "Prestige+", "Luxury", "Luxury+"],
  },
  "Mahindra": {
    "Bolero": ["B2", "B4", "B6", "B8", "B6 (O)", "B8 (O)"],
    "KUV100": ["K2", "K2+", "K4", "K4+", "K6", "K6+"],
    "XUV300": ["W4", "W6", "W8", "W8 (O)"],
    "XUV 3XO": ["MX1", "MX2", "MX2 Pro", "MX3", "MX3 Pro", "AX5", "AX5 L", "AX7", "AX7 L"],
    "XUV700": ["MX", "AX3", "AX5", "AX7", "AX7 L", "AX7 Ultimate"],
    "Scorpio": ["S3", "S5", "S7", "S9", "S11"],
    "Scorpio-N": ["Z2", "Z4", "Z6", "Z8", "Z8 L"],
    "Thar": ["AX STD", "AX (O) MT", "AX (O) AT", "LX Hard Top", "LX AT Hard Top"],
    "BE 6e": ["Pack One", "Pack Two", "Pack Three"],
    "XEV 9e": ["Pack One", "Pack Two", "Pack Three"],
  },
  "Toyota": {
    "Etios": ["J", "G", "V", "V (O)", "GD", "VD"],
    "Liva": ["J", "G", "V", "V (O)"],
    "Glanza": ["E", "S", "V", "G", "S AMT", "G AMT"],
    "Urban Cruiser": ["Mid", "High", "Premium"],
    "Urban Cruiser Hyryder": ["E", "S", "G", "V", "Advanced", "E Hybrid", "S Hybrid", "G Hybrid"],
    "Innova Crysta": ["GX MT", "GX AT", "VX MT", "VX AT", "ZX MT", "ZX AT"],
    "Innova Hycross": ["GX", "GX (O)", "VX", "VX (O)", "ZX", "ZX (O)"],
    "Fortuner": ["2.7 4x2 MT", "2.7 4x2 AT", "2.8 4x2 AT", "2.8 4x4 AT", "Legender 4x2", "Legender 4x4"],
    "Camry": ["Hybrid", "Hybrid Premium"],
    "Hilux": ["STD", "High"],
  },
  "Volkswagen": {
    "Polo": ["Trendline", "Comfortline", "Highline", "GT TSI"],
    "Vento": ["Trendline", "Comfortline", "Highline Plus", "Highline Plus AT"],
    "Taigun": ["Trendline", "Comfortline", "Highline", "GT", "GT Plus"],
    "Virtus": ["Dynamic", "Exclusive", "GT", "GT Plus"],
  },
  "Skoda": {
    "Rapid": ["Ambition", "Style", "Monte Carlo"],
    "Octavia": ["Ambition", "Style", "RS 245"],
    "Superb": ["L&K"],
    "Kushaq": ["Active", "Ambition", "Style", "Monte Carlo"],
    "Slavia": ["Active", "Ambition", "Style", "Monte Carlo"],
    "Kodiaq": ["Style", "L&K", "Sportline"],
  },
  "MG": {
    "Hector": ["Style", "Super", "Smart", "Sharp", "Savvy"],
    "Hector Plus": ["Super", "Smart", "Sharp 6-Seat", "Savvy 6-Seat", "Sharp 7-Seat", "Savvy 7-Seat"],
    "Astor": ["Style", "Super", "Smart", "Sharp Pro", "Savvy"],
    "ZS EV": ["Excite", "Exclusive"],
    "Comet EV": ["Pace", "Play", "Plush"],
    "Windsor EV": ["Excite Pro", "Exclusive Pro", "Essence Pro"],
  },
  "Renault": {
    "Kwid": ["STD", "RXE", "RXL", "RXT", "RXT (O)", "Climber"],
    "Triber": ["RXE", "RXL", "RXZ", "RXZ (O)", "RXZ AMT"],
    "Kiger": ["RXE", "RXL", "RXT", "RXZ", "RXZ Turbo", "RXT AMT", "RXZ AMT"],
    "Duster": ["RxE", "RxL 85", "RxL 110", "RxZ 110", "RxZ AWD", "Turbo RXZ"],
  },
  "Nissan": {
    "Micra": ["XE", "XL", "XV", "XV Premium"],
    "Sunny": ["XE", "XL", "XV", "XV CVT"],
    "Kicks": ["XL", "XV", "XV Premium"],
    "Magnite": ["XE", "XL", "XV", "XV Premium", "Turbo XV", "Turbo XV Premium", "Turbo XV Premium AMT"],
  },
  "Ford": {
    "Figo": ["Ambiente", "Trend", "Trend+", "Titanium", "Titanium+"],
    "Aspire": ["Ambiente", "Trend", "Titanium", "Titanium+"],
    "EcoSport": ["Ambiente", "Trend", "Trend+", "Titanium", "Titanium+", "S"],
    "Endeavour": ["Trend 2.0 AT 4x2", "Titanium 2.0 AT 4x2", "Titanium+ 2.0 AT 4x4"],
  },
  "Jeep": {
    "Compass": ["Sport", "Sport+", "Longitude", "Longitude+", "Limited", "Limited+", "Model S"],
    "Meridian": ["Longitude", "Longitude+", "Limited", "Limited (O)"],
    "Wrangler": ["Unlimited Sport", "Unlimited Sahara"],
  },
  "BMW": {
    "3 Series": ["320d Sport", "320d Luxury", "320d M Sport", "330i M Sport", "M340i"],
    "5 Series": ["520d Luxury", "520d M Sport", "530d M Sport", "540i M Sport"],
    "X1": ["sDrive18i", "sDrive20d", "xDrive20d"],
    "X3": ["xDrive20i", "xDrive30i", "xDrive20d", "M40i"],
    "X5": ["xDrive30d", "xDrive40i", "xDrive30d MHEV"],
  },
  "Mercedes-Benz": {
    "A-Class": ["A 200", "A 200 d", "AMG A 35"],
    "C-Class": ["C 200", "C 220 d", "AMG C 43"],
    "E-Class": ["E 200", "E 220 d", "E 350 d", "AMG E 53"],
    "GLA": ["GLA 200", "GLA 220 d", "AMG GLA 35"],
    "GLC": ["GLC 220 d", "GLC 300", "AMG GLC 43"],
  },
  "Audi": {
    "A4": ["Premium", "Premium Plus", "Technology"],
    "A6": ["Premium", "Technology"],
    "Q3": ["Premium", "Premium Plus", "Technology"],
    "Q5": ["Premium", "Premium Plus", "Technology"],
    "Q7": ["Premium", "Premium Plus", "Technology"],
  },
};

const MAKES = Object.keys(CAR_DATABASE).sort();

const FUEL_TYPES = ["Petrol", "Diesel", "CNG", "Electric", "Hybrid (Petrol)", "Hybrid (Diesel)"];
const TRANSMISSIONS = ["Manual", "Automatic (AT)", "AMT", "CVT", "DCT", "IMT"];
const YEARS = Array.from({ length: new Date().getFullYear() - 2004 + 1 }, (_, i) => String(new Date().getFullYear() - i));

// ── Interfaces ────────────────────────────────────────────────────────────────

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
  variant: string;
  year: string;
  fuel_type: string;
  transmission: string;
  listing_price: string;
  odometer_reading: string;
  city: string;
  service_entries: ServiceEntry[];
  insurance_claims: InsuranceClaim[];
  seller_claims_clean_history: boolean;
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

// ── Style maps ────────────────────────────────────────────────────────────────

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

// ── Helpers ───────────────────────────────────────────────────────────────────

const emptyService = (): ServiceEntry => ({ date: "", odometer: "", items: "", workshop: "" });
const emptyClaim = (): InsuranceClaim => ({ year: "", amount: "", description: "" });

const HIDDEN_DIMENSIONS = new Set(["ownership"]);

// ── Page component ────────────────────────────────────────────────────────────

export default function AssessPage() {
  const [form, setForm] = useState<FormData>({
    make: "",
    model: "",
    variant: "",
    year: "",
    fuel_type: "",
    transmission: "",
    listing_price: "",
    odometer_reading: "",
    city: "",
    service_entries: [emptyService()],
    insurance_claims: [],
    seller_claims_clean_history: false,
    seller_loan_disclosure: "not_mentioned",
  });

  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<TrustReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  function setField<K extends keyof FormData>(key: K, value: FormData[K]) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function onMakeChange(make: string) {
    setForm((prev) => ({ ...prev, make, model: "", variant: "" }));
  }

  function onModelChange(model: string) {
    setForm((prev) => ({ ...prev, model, variant: "" }));
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

  const models = form.make ? Object.keys(CAR_DATABASE[form.make] ?? {}).sort() : [];
  const variants = form.make && form.model ? (CAR_DATABASE[form.make]?.[form.model] ?? []) : [];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setReport(null);

    try {
      const res = await fetch("/api/assess", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...form,
          fuel_type: form.fuel_type.toLowerCase().replace(/\s*\(.*\)/, ""),
          transmission: form.transmission.toLowerCase().split(" ")[0],
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Assessment failed" }));
        throw new Error(err.detail || "Assessment failed");
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
  const visibleAssessments = report?.assessments.filter((a) => !HIDDEN_DIMENSIONS.has(a.dimension)) ?? [];

  return (
    <>
      <Navbar />
      <main className="min-h-screen pt-20 pb-16">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">
          {!report ? (
            <>
              <div className="text-center mb-10 pt-8">
                <h1 className="text-3xl sm:text-4xl font-bold text-white mb-3">
                  Assess a Used Car
                </h1>
                <p className="text-slate-400 max-w-xl mx-auto">
                  Fill in the details below. The more data you provide, the more
                  accurate and actionable your trust report will be.
                </p>
              </div>

              <form onSubmit={handleSubmit} className="flex flex-col gap-6">

                {/* ── Vehicle Identity ─────────────────────────────────── */}
                <Section title="Vehicle Details">
                  <div className="grid sm:grid-cols-3 gap-4">
                    {/* Make */}
                    <Field label="Make *" required>
                      <select
                        required
                        value={form.make}
                        onChange={(e) => onMakeChange(e.target.value)}
                      >
                        <option value="">Select make</option>
                        {MAKES.map((m) => (
                          <option key={m} value={m}>{m}</option>
                        ))}
                      </select>
                    </Field>

                    {/* Model */}
                    <Field label="Model *" required>
                      <select
                        required
                        value={form.model}
                        onChange={(e) => onModelChange(e.target.value)}
                        disabled={!form.make}
                      >
                        <option value="">Select model</option>
                        {models.map((m) => (
                          <option key={m} value={m}>{m}</option>
                        ))}
                      </select>
                    </Field>

                    {/* Variant */}
                    <Field label="Variant">
                      <select
                        value={form.variant}
                        onChange={(e) => setField("variant", e.target.value)}
                        disabled={!form.model || variants.length === 0}
                      >
                        <option value="">Select variant</option>
                        {variants.map((v) => (
                          <option key={v} value={v}>{v}</option>
                        ))}
                      </select>
                    </Field>

                    {/* Year */}
                    <Field label="Manufacturing Year *" required>
                      <select
                        required
                        value={form.year}
                        onChange={(e) => setField("year", e.target.value)}
                      >
                        <option value="">Select year</option>
                        {YEARS.map((y) => (
                          <option key={y} value={y}>{y}</option>
                        ))}
                      </select>
                    </Field>

                    {/* Fuel type */}
                    <Field label="Fuel Type *" required>
                      <select
                        required
                        value={form.fuel_type}
                        onChange={(e) => setField("fuel_type", e.target.value)}
                      >
                        <option value="">Select fuel type</option>
                        {FUEL_TYPES.map((f) => (
                          <option key={f} value={f}>{f}</option>
                        ))}
                      </select>
                    </Field>

                    {/* Transmission */}
                    <Field label="Transmission *" required>
                      <select
                        required
                        value={form.transmission}
                        onChange={(e) => setField("transmission", e.target.value)}
                      >
                        <option value="">Select transmission</option>
                        {TRANSMISSIONS.map((t) => (
                          <option key={t} value={t}>{t}</option>
                        ))}
                      </select>
                    </Field>
                  </div>

                  <div className="grid sm:grid-cols-3 gap-4 mt-4">
                    {/* Asking price */}
                    <Field label="Asking Price (Rs.) *" required>
                      <input
                        required
                        type="number"
                        min="10000"
                        placeholder="e.g. 520000"
                        value={form.listing_price}
                        onChange={(e) => setField("listing_price", e.target.value)}
                      />
                    </Field>

                    {/* Odometer */}
                    <Field label="Odometer Reading (km) *" required>
                      <input
                        required
                        type="number"
                        min="0"
                        placeholder="e.g. 45000"
                        value={form.odometer_reading}
                        onChange={(e) => setField("odometer_reading", e.target.value)}
                      />
                    </Field>

                    {/* City */}
                    <Field label="City of Purchase">
                      <input
                        placeholder="e.g. Mumbai"
                        value={form.city}
                        onChange={(e) => setField("city", e.target.value)}
                      />
                    </Field>
                  </div>
                </Section>

                {/* ── Service History ──────────────────────────────────── */}
                <Section title="Service History">
                  <p className="text-xs text-slate-500 mb-4">
                    Add entries from the service book or stamped records. Authorised
                    service centre history carries the most weight. Enter the work
                    done as a comma-separated list (e.g.{" "}
                    <em>oil change, air filter, brake pads</em>).
                  </p>
                  {form.service_entries.map((entry, i) => (
                    <div key={i} className="grid sm:grid-cols-4 gap-3 mb-3 pb-3 border-b border-white/5 last:border-0 last:pb-0">
                      <Field label={`Service ${i + 1} — Date`}>
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
                          placeholder="oil change, brakes…"
                          value={entry.items}
                          onChange={(e) => updateService(i, "items", e.target.value)}
                        />
                      </Field>
                      <Field label="Workshop / Centre">
                        <input
                          placeholder="ASC / local garage"
                          value={entry.workshop}
                          onChange={(e) => updateService(i, "workshop", e.target.value)}
                        />
                      </Field>
                    </div>
                  ))}
                  <div className="flex gap-4 mt-2">
                    <button
                      type="button"
                      onClick={() => setField("service_entries", [...form.service_entries, emptyService()])}
                      className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
                    >
                      + Add service entry
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

                {/* ── Insurance / Accident Claims ───────────────────────── */}
                <Section title="Insurance & Accident Claims">
                  <p className="text-xs text-slate-500 mb-4">
                    Add any known insurance claims from the seller or policy
                    document. A claim amount above Rs.&nbsp;50,000 is flagged as a
                    major incident. Leave this section empty if no claims are known.
                  </p>
                  {form.insurance_claims.map((claim, i) => (
                    <div key={i} className="grid sm:grid-cols-3 gap-3 mb-3 pb-3 border-b border-white/5 last:border-0 last:pb-0">
                      <Field label={`Claim ${i + 1} — Year`}>
                        <select
                          value={claim.year}
                          onChange={(e) => updateClaim(i, "year", e.target.value)}
                        >
                          <option value="">Select year</option>
                          {YEARS.map((y) => (
                            <option key={y} value={y}>{y}</option>
                          ))}
                        </select>
                      </Field>
                      <Field label="Claim Amount (Rs.)">
                        <input
                          type="number"
                          placeholder="e.g. 45000"
                          value={claim.amount}
                          onChange={(e) => updateClaim(i, "amount", e.target.value)}
                        />
                      </Field>
                      <Field label="Nature of Claim">
                        <input
                          placeholder="e.g. rear collision, flood"
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

                {/* ── Seller Disclosures ────────────────────────────────── */}
                <Section title="Seller Disclosures">
                  <p className="text-xs text-slate-500 mb-4">
                    Record what the seller has verbally or formally claimed. These
                    are weighted at low confidence but used to detect contradictions
                    with physical evidence.
                  </p>
                  <div className="flex flex-col gap-4">
                    <label className="flex items-start gap-3 cursor-pointer group">
                      <input
                        type="checkbox"
                        checked={form.seller_claims_clean_history}
                        onChange={(e) => setField("seller_claims_clean_history", e.target.checked)}
                        className="w-4 h-4 mt-0.5 accent-orange-500 flex-shrink-0"
                      />
                      <div>
                        <span className="text-sm text-slate-300 group-hover:text-white transition-colors">
                          Seller claims no accident history
                        </span>
                        <p className="text-xs text-slate-500 mt-0.5">
                          Cross-referenced against service records and insurance data.
                        </p>
                      </div>
                    </label>

                    <Field label="Loan / Hypothecation Disclosure">
                      <select
                        value={form.seller_loan_disclosure}
                        onChange={(e) => setField("seller_loan_disclosure", e.target.value)}
                      >
                        <option value="not_mentioned">Seller did not mention any loan</option>
                        <option value="denied">Seller explicitly denied any outstanding loan</option>
                        <option value="acknowledged">Seller acknowledged an active loan</option>
                        <option value="closure_plan">Seller provided a loan closure plan before handover</option>
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
                      Analysing…
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
                      <span className="text-base font-normal text-slate-400">/100</span>
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

              {/* Dimension breakdown — ownership hidden */}
              <h2 className="text-lg font-semibold text-white mb-4">Dimension Breakdown</h2>
              <div className="flex flex-col gap-3 mb-8">
                {visibleAssessments.map((a) => (
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
                        <div key={f.flag_id} className="mb-2 flex items-start gap-2">
                          <span className={`flex-shrink-0 text-xs px-2 py-0.5 rounded-full ${SEV_COLOR[f.severity] ?? SEV_COLOR.low}`}>
                            {f.severity}
                          </span>
                          <span className="text-sm text-slate-300">{f.description}</span>
                        </div>
                      ))}
                    </div>
                  </details>
                ))}
              </div>

              {/* Contradictions */}
              {report.contradictions.length > 0 && (
                <div className="mb-8">
                  <h2 className="text-lg font-semibold text-white mb-4">Contradictions Detected</h2>
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
                  <h2 className="text-lg font-semibold text-white mb-4">Action Checklist</h2>
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
                    Rs.&nbsp;{report.cost_estimate.total_low.toLocaleString("en-IN")} –{" "}
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

// ── Sub-components ────────────────────────────────────────────────────────────

function Section({ title, children }: { title: string; children: React.ReactNode }) {
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
  const baseClass =
    "w-full bg-[#070d1a] border border-white/12 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-orange-500/50 disabled:opacity-40";

  const child = children as React.ReactElement<
    React.InputHTMLAttributes<HTMLInputElement> & React.SelectHTMLAttributes<HTMLSelectElement>
  >;
  const isSelect = child.type === "select";

  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs text-slate-400">
        {label}
        {required && <span className="text-orange-400 ml-0.5">*</span>}
      </label>
      <child.type
        {...child.props}
        className={isSelect ? `${baseClass} appearance-none` : baseClass}
      />
    </div>
  );
}
