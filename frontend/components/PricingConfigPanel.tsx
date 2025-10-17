"use client";

import { useEffect, useState } from "react";
import { fetchPricingConfig } from "../lib/api";

interface PricingParameterGroup {
  label: string;
  keys: string[];
}

const groups: PricingParameterGroup[] = [
  { label: "Densities", keys: ["density"] },
  { label: "Material costs", keys: ["material_cost_per_g"] },
  {
    label: "Operational",
    keys: [
      "machine_rate_eur_per_hour",
      "base_fee_eur",
      "post_rate_eur_per_minute",
      "risk_multiplier",
      "minimum_item_price_eur",
      "minimum_order_price_eur",
      "setup_time_hours",
    ],
  },
];

export function PricingConfigPanel() {
  const [config, setConfig] = useState<Record<string, unknown> | null>(null);
  const [meta, setMeta] = useState<{ version: string; effective_from: string; created_by: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPricingConfig()
      .then((data) => {
        setConfig(data.parameters);
        setMeta({ version: data.version, effective_from: data.effective_from, created_by: data.created_by });
      })
      .catch(() => setError("Unable to load pricing configuration"));
  }, []);

  return (
    <section className="space-y-4 rounded-2xl bg-white p-6 shadow-md">
      <header>
        <h2 className="text-2xl font-semibold text-brand-primary">Pricing configuration</h2>
        {meta && (
          <p className="text-xs text-brand-muted">
            v{meta.version} · Effective {new Date(meta.effective_from).toLocaleDateString()} · Last updated by {meta.created_by}
          </p>
        )}
      </header>
      {error && <p className="text-sm text-red-500">{error}</p>}
      {config ? (
        <div className="grid gap-4 md:grid-cols-2">
          {groups.map((group) => (
            <div key={group.label} className="space-y-2 rounded-lg border border-slate-200 p-4">
              <h3 className="text-lg font-semibold text-brand-primary">{group.label}</h3>
              <ul className="space-y-1 text-sm text-brand-muted">
                {group.keys.map((key) => {
                  const value = config[key];
                  if (value && typeof value === "object") {
                    return (
                      <li key={key}>
                        <span className="font-medium text-brand-primary">{key}</span>
                        <ul className="ml-3 list-disc space-y-1 pl-3">
                          {Object.entries(value as Record<string, number>).map(([subKey, subValue]) => (
                            <li key={subKey}>
                              <span className="capitalize">{subKey}</span>: {subValue}
                            </li>
                          ))}
                        </ul>
                      </li>
                    );
                  }
                  return (
                    <li key={key}>
                      <span className="capitalize">{key.replace(/_/g, " ")}</span>: {String(value)}
                    </li>
                  );
                })}
              </ul>
              <button className="rounded-md border border-brand-accent px-3 py-2 text-xs font-semibold text-brand-accent hover:bg-emerald-50">
                Edit
              </button>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-sm text-brand-muted">Loading configuration...</p>
      )}
    </section>
  );
}
