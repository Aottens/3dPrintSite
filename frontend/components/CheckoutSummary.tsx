"use client";

import { useState } from "react";
import { createOrder } from "../lib/api";
import { useCartStore } from "../lib/store";
import { useAuthStore } from "../lib/store";

export function CheckoutSummary() {
  const { items, removeItem, clearCart, getTotalPrice } = useCartStore();
  const { isAuthenticated } = useAuthStore();

  const [street, setStreet] = useState("");
  const [city, setCity] = useState("");
  const [postalCode, setPostalCode] = useState("");
  const [country, setCountry] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [orderNumber, setOrderNumber] = useState<string | null>(null);

  async function handleCheckout() {
    if (!street || !city || !postalCode || !country) {
      setError("Please fill in all shipping address fields");
      return;
    }

    if (items.length === 0) {
      setError("Cart is empty");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const order = await createOrder(
        items.map((item) => item.quote.id),
        {
          street,
          city,
          postal_code: postalCode,
          country,
          company_name: companyName || undefined,
        }
      );

      setOrderNumber(order.order_number);
      clearCart();

      // Reset form
      setStreet("");
      setCity("");
      setPostalCode("");
      setCountry("");
      setCompanyName("");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create order");
    } finally {
      setIsLoading(false);
    }
  }

  if (orderNumber) {
    return (
      <section className="space-y-4 rounded-2xl bg-white p-6 shadow-md">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-brand-primary">
            Order Placed!
          </h2>
          <p className="mt-2 text-brand-muted">
            Your order number is{" "}
            <span className="font-semibold text-brand-accent">{orderNumber}</span>
          </p>
          <button
            onClick={() => setOrderNumber(null)}
            className="mt-4 rounded-md bg-brand-accent px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-500"
          >
            Place another order
          </button>
        </div>
      </section>
    );
  }

  const subtotal = getTotalPrice();

  return (
    <section className="space-y-4 rounded-2xl bg-white p-6 shadow-md">
      <header>
        <h2 className="text-2xl font-semibold text-brand-primary">
          Cart &amp; checkout
        </h2>
        <p className="text-xs text-brand-muted">
          Review items, enter shipping, and place your order.
        </p>
      </header>

      {!isAuthenticated && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-md text-sm text-amber-800">
          Please log in to checkout.
        </div>
      )}

      <div className="space-y-4">
        {items.length === 0 ? (
          <p className="text-sm text-brand-muted">Your cart is empty.</p>
        ) : (
          <ul className="space-y-3 text-sm">
            {items.map((item) => (
              <li
                key={item.quote.id}
                className="flex items-center justify-between rounded-md border border-slate-200 p-3"
              >
                <div>
                  <p className="font-medium text-brand-primary">
                    {item.quote.material_name}
                  </p>
                  <p className="text-xs text-brand-muted">
                    {item.quote.color_name} · {item.quote.profile_name}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="font-semibold">
                      € {item.quote.total_price.toFixed(2)}
                    </p>
                    <p className="text-xs text-brand-muted">
                      {item.quote.quantity} × € {item.quote.unit_price.toFixed(2)}
                    </p>
                  </div>
                  <button
                    onClick={() => removeItem(item.quote.id)}
                    className="text-red-500 hover:text-red-700"
                  >
                    &times;
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}

        {items.length > 0 && (
          <div className="flex flex-col gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm">
            <label className="flex flex-col gap-1">
              <span className="text-xs font-semibold uppercase text-brand-muted">
                Company (optional)
              </span>
              <input
                className="rounded-md border border-slate-200 px-3 py-2"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Company name"
              />
            </label>
            <label className="flex flex-col gap-1">
              <span className="text-xs font-semibold uppercase text-brand-muted">
                Street address
              </span>
              <input
                className="rounded-md border border-slate-200 px-3 py-2"
                value={street}
                onChange={(e) => setStreet(e.target.value)}
                placeholder="Street and number"
                required
              />
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="flex flex-col gap-1">
                <span className="text-xs font-semibold uppercase text-brand-muted">
                  Postal code
                </span>
                <input
                  className="rounded-md border border-slate-200 px-3 py-2"
                  value={postalCode}
                  onChange={(e) => setPostalCode(e.target.value)}
                  placeholder="12345"
                  required
                />
              </label>
              <label className="flex flex-col gap-1">
                <span className="text-xs font-semibold uppercase text-brand-muted">
                  City
                </span>
                <input
                  className="rounded-md border border-slate-200 px-3 py-2"
                  value={city}
                  onChange={(e) => setCity(e.target.value)}
                  placeholder="City"
                  required
                />
              </label>
            </div>
            <label className="flex flex-col gap-1">
              <span className="text-xs font-semibold uppercase text-brand-muted">
                Country
              </span>
              <input
                className="rounded-md border border-slate-200 px-3 py-2"
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                placeholder="Country"
                required
              />
            </label>

            {error && <p className="text-sm text-red-500">{error}</p>}

            <button
              onClick={handleCheckout}
              disabled={isLoading || !isAuthenticated}
              className="rounded-md bg-brand-accent px-4 py-2 text-sm font-semibold text-white shadow hover:bg-emerald-500 disabled:opacity-50"
            >
              {isLoading ? "Processing..." : "Place order"}
            </button>
          </div>
        )}

        <div className="flex items-center justify-between text-sm font-semibold text-brand-primary">
          <span>Subtotal</span>
          <span>€ {subtotal.toFixed(2)}</span>
        </div>
      </div>
    </section>
  );
}
