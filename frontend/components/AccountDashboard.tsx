const mockHistory = [
  { id: 90, status: "shipped", total: 128.4, tracking: "TRACK123", updated: "2024-01-22" },
  { id: 91, status: "processing", total: 64.2, tracking: null, updated: "2024-02-05" },
];

export function AccountDashboard() {
  return (
    <section className="space-y-4 rounded-2xl bg-white p-6 shadow-md">
      <header className="flex flex-col gap-1">
        <h2 className="text-2xl font-semibold text-brand-primary">Account dashboard</h2>
        <p className="text-xs text-brand-muted">Access recent orders, invoices, and account preferences.</p>
      </header>
      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-3 rounded-lg border border-slate-200 p-4">
          <h3 className="text-lg font-semibold text-brand-primary">Recent orders</h3>
          <ul className="space-y-2 text-sm">
            {mockHistory.map((order) => (
              <li key={order.id} className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-brand-primary">Order #{order.id}</p>
                  <p className="text-xs text-brand-muted">Updated {order.updated}</p>
                </div>
                <div className="text-right text-xs uppercase text-brand-muted">
                  <p>{order.status}</p>
                  {order.tracking ? <p>{order.tracking}</p> : <p className="text-amber-500">Pending tracking</p>}
                </div>
              </li>
            ))}
          </ul>
          <button className="rounded-md border border-slate-200 px-3 py-2 text-xs font-semibold text-brand-primary hover:border-brand-accent">
            View all orders
          </button>
        </div>
        <div className="space-y-3 rounded-lg border border-slate-200 p-4">
          <h3 className="text-lg font-semibold text-brand-primary">Profile</h3>
          <form className="space-y-3 text-sm">
            <label className="flex flex-col gap-1">
              <span className="text-xs font-semibold uppercase text-brand-muted">Company name</span>
              <input className="rounded-md border border-slate-200 px-3 py-2" defaultValue="NovaPrint Labs" />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs font-semibold uppercase text-brand-muted">VAT number</span>
              <input className="rounded-md border border-slate-200 px-3 py-2" defaultValue="NL123456789B01" />
            </label>
            <button className="rounded-md bg-brand-accent px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-500">
              Save changes
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}
