"use client";

import { useEffect, useState } from "react";
import { fetchAnalytics, type AnalyticsSummary } from "../lib/api";
import { useAuthStore } from "../lib/store";

export function AdminAnalytics() {
  const { user } = useAuthStore();
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user?.role === "admin") {
      fetchAnalytics()
        .then(setAnalytics)
        .catch(() => setError("Unable to load analytics"));
    }
  }, [user]);

  if (user?.role !== "admin") {
    return null;
  }

  const metrics = analytics
    ? [
        {
          label: "Orders (7d)",
          value: analytics.orders_7d.toString(),
          trend: "",
        },
        {
          label: "Revenue (7d)",
          value: `€ ${analytics.revenue_7d.toLocaleString()}`,
          trend: "",
        },
        {
          label: "Top material",
          value: analytics.top_material,
          trend: `${analytics.top_material_orders} orders`,
        },
        {
          label: "Avg. lead time",
          value: `${analytics.avg_lead_time_days} days`,
          trend: "",
        },
      ]
    : [
        { label: "Orders (7d)", value: "—", trend: "" },
        { label: "Revenue (7d)", value: "—", trend: "" },
        { label: "Top material", value: "—", trend: "" },
        { label: "Avg. lead time", value: "—", trend: "" },
      ];

  return (
    <section className="rounded-2xl bg-white p-6 shadow-md">
      <h2 className="text-2xl font-semibold text-brand-primary">
        Analytics dashboard
      </h2>
      {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <div
            key={metric.label}
            className="rounded-lg border border-slate-200 bg-slate-50 p-4"
          >
            <p className="text-xs font-semibold uppercase text-brand-muted">
              {metric.label}
            </p>
            <p className="mt-2 text-xl font-semibold text-brand-primary">
              {metric.value}
            </p>
            {metric.trend && (
              <p className="text-xs text-emerald-600">{metric.trend}</p>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}
