const mockCart = [
  {
    id: 1,
    name: "Gearbox housing",
    material: "PETG",
    unitPrice: 32.5,
    quantity: 3,
  },
  {
    id: 2,
    name: "Sensor mount",
    material: "ASA",
    unitPrice: 18.75,
    quantity: 2,
  },
];

const subtotal = mockCart.reduce((sum, item) => sum + item.unitPrice * item.quantity, 0);

export function CheckoutSummary() {
  return (
    <section className="space-y-4 rounded-2xl bg-white p-6 shadow-md">
      <header>
        <h2 className="text-2xl font-semibold text-brand-primary">Cart &amp; checkout</h2>
        <p className="text-xs text-brand-muted">Review items, enter shipping, and hand-off to payment gateway.</p>
      </header>
      <div className="space-y-4">
        <ul className="space-y-3 text-sm">
          {mockCart.map((item) => (
            <li key={item.id} className="flex items-center justify-between rounded-md border border-slate-200 p-3">
              <div>
                <p className="font-medium text-brand-primary">{item.name}</p>
                <p className="text-xs text-brand-muted">{item.material}</p>
              </div>
              <div className="text-right">
                <p className="font-semibold">€ {(item.unitPrice * item.quantity).toFixed(2)}</p>
                <p className="text-xs text-brand-muted">{item.quantity} × € {item.unitPrice.toFixed(2)}</p>
              </div>
            </li>
          ))}
        </ul>
        <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm">
          <label className="flex flex-col gap-1">
            <span className="text-xs font-semibold uppercase text-brand-muted">Shipping address</span>
            <textarea className="rounded-md border border-slate-200 p-2" rows={3} placeholder="Company · Street · City" />
          </label>
          <button className="rounded-md bg-brand-accent px-4 py-2 text-sm font-semibold text-white shadow hover:bg-emerald-500">
            Continue to payment
          </button>
        </div>
        <div className="flex items-center justify-between text-sm font-semibold text-brand-primary">
          <span>Subtotal</span>
          <span>€ {subtotal.toFixed(2)}</span>
        </div>
      </div>
    </section>
  );
}
