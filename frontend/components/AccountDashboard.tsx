"use client";

import { useEffect, useState } from "react";
import { fetchOrders, type OrderListItem } from "../lib/api";
import { useAuthStore } from "../lib/store";

export function AccountDashboard() {
  const { user, isAuthenticated } = useAuthStore();
  const [orders, setOrders] = useState<OrderListItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      loadOrders();
    }
  }, [isAuthenticated]);

  async function loadOrders() {
    setIsLoading(true);
    try {
      const data = await fetchOrders();
      setOrders(data.slice(0, 5)); // Show only recent 5
    } catch {
      // Silently fail
    } finally {
      setIsLoading(false);
    }
  }

  if (!isAuthenticated) {
    return (
      <section className="space-y-4 rounded-2xl bg-white p-6 shadow-md">
        <h2 className="text-2xl font-semibold text-brand-primary">
          Account dashboard
        </h2>
        <p className="text-sm text-brand-muted">
          Log in to view your orders and account settings.
        </p>
      </section>
    );
  }

  return (
    <section className="space-y-4 rounded-2xl bg-white p-6 shadow-md">
      <header className="flex flex-col gap-1">
        <h2 className="text-2xl font-semibold text-brand-primary">
          Account dashboard
        </h2>
        <p className="text-xs text-brand-muted">
          Welcome back, {user?.name}
        </p>
      </header>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="space-y-3 rounded-lg border border-slate-200 p-4">
          <h3 className="text-lg font-semibold text-brand-primary">
            Recent orders
          </h3>
          {isLoading ? (
            <p className="text-sm text-brand-muted">Loading...</p>
          ) : orders.length === 0 ? (
            <p className="text-sm text-brand-muted">No orders yet.</p>
          ) : (
            <ul className="space-y-2 text-sm">
              {orders.map((order) => (
                <li
                  key={order.id}
                  className="flex items-center justify-between"
                >
                  <div>
                    <p className="font-medium text-brand-primary">
                      {order.order_number}
                    </p>
                    <p className="text-xs text-brand-muted">
                      {new Date(order.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="text-right text-xs">
                    <p className="uppercase text-brand-muted">{order.status.replace(/_/g, " ")}</p>
                    <p className="font-medium">€ {order.total_price.toFixed(2)}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="space-y-3 rounded-lg border border-slate-200 p-4">
          <h3 className="text-lg font-semibold text-brand-primary">Profile</h3>
          <div className="space-y-2 text-sm">
            <div>
              <span className="text-brand-muted">Email: </span>
              <span className="font-medium">{user?.email}</span>
            </div>
            <div>
              <span className="text-brand-muted">Company: </span>
              <span className="font-medium">{user?.company_name || "—"}</span>
            </div>
            <div>
              <span className="text-brand-muted">Role: </span>
              <span className="font-medium capitalize">{user?.role}</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
