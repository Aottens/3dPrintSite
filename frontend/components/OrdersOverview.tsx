const mockOrders = [
  {
    id: 101,
    status: "processing",
    customer: "Alice Robotics",
    material: "PETG",
    total: 245.5,
    submitted: "2024-02-01",
  },
  {
    id: 102,
    status: "ready-to-ship",
    customer: "Bright Labs",
    material: "PLA",
    total: 89.0,
    submitted: "2024-02-03",
  },
];

const statusStyles: Record<string, string> = {
  processing: "bg-amber-100 text-amber-800",
  "ready-to-ship": "bg-emerald-100 text-emerald-700",
  shipped: "bg-slate-200 text-slate-700",
};

export function OrdersOverview() {
  return (
    <section className="space-y-4 rounded-2xl bg-white p-6 shadow-md">
      <header className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-brand-primary">Orders overview</h2>
          <p className="text-xs text-brand-muted">Monitor status across printers and trigger notifications.</p>
        </div>
        <button className="rounded-md border border-slate-200 px-4 py-2 text-xs font-semibold text-brand-primary hover:border-brand-accent">
          Export CSV
        </button>
      </header>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left font-semibold uppercase tracking-wide text-xs text-brand-muted">Order</th>
              <th className="px-3 py-2 text-left font-semibold uppercase tracking-wide text-xs text-brand-muted">Customer</th>
              <th className="px-3 py-2 text-left font-semibold uppercase tracking-wide text-xs text-brand-muted">Material</th>
              <th className="px-3 py-2 text-left font-semibold uppercase tracking-wide text-xs text-brand-muted">Total</th>
              <th className="px-3 py-2 text-left font-semibold uppercase tracking-wide text-xs text-brand-muted">Submitted</th>
              <th className="px-3 py-2 text-left font-semibold uppercase tracking-wide text-xs text-brand-muted">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {mockOrders.map((order) => (
              <tr key={order.id}>
                <td className="px-3 py-2 font-medium text-brand-primary">#{order.id}</td>
                <td className="px-3 py-2">{order.customer}</td>
                <td className="px-3 py-2">{order.material}</td>
                <td className="px-3 py-2">€ {order.total.toFixed(2)}</td>
                <td className="px-3 py-2">{order.submitted}</td>
                <td className="px-3 py-2">
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${statusStyles[order.status] ?? "bg-slate-200 text-slate-700"}`}
                  >
                    {order.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
