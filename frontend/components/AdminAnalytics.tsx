const metrics = [
  { label: "Orders (7d)", value: "42", trend: "+12%" },
  { label: "Revenue (7d)", value: "€ 6,420", trend: "+8%" },
  { label: "Top material", value: "PETG", trend: "36 orders" },
  { label: "Avg. lead time", value: "3.2 days", trend: "-0.4" },
];

export function AdminAnalytics() {
  return (
    <section className="rounded-2xl bg-white p-6 shadow-md">
      <h2 className="text-2xl font-semibold text-brand-primary">Analytics dashboard</h2>
      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((metric) => (
          <div key={metric.label} className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <p className="text-xs font-semibold uppercase text-brand-muted">{metric.label}</p>
            <p className="mt-2 text-xl font-semibold text-brand-primary">{metric.value}</p>
            <p className="text-xs text-emerald-600">{metric.trend}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
