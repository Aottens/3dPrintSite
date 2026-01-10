"use client";

import { useEffect, useState } from "react";
import { fetchAllOrders, updateOrderStatus, exportOrdersCsv, type Order } from "../lib/api";
import { useAuthStore } from "../lib/store";

const statusStyles: Record<string, string> = {
  new: "bg-blue-100 text-blue-800",
  in_planning: "bg-purple-100 text-purple-800",
  in_print: "bg-amber-100 text-amber-800",
  post_processing: "bg-orange-100 text-orange-800",
  shipped: "bg-emerald-100 text-emerald-700",
  completed: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
};

const statusOptions = [
  "new",
  "in_planning",
  "in_print",
  "post_processing",
  "shipped",
  "completed",
  "cancelled",
];

export function OrdersOverview() {
  const { user } = useAuthStore();
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  useEffect(() => {
    if (user?.role === "admin") {
      loadOrders();
    }
  }, [user]);

  async function loadOrders() {
    setIsLoading(true);
    try {
      const data = await fetchAllOrders();
      setOrders(data);
    } catch {
      setError("Unable to load orders");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleStatusChange(orderId: string, newStatus: string) {
    setUpdatingId(orderId);
    try {
      const updated = await updateOrderStatus(orderId, newStatus);
      setOrders((prev) =>
        prev.map((o) => (o.id === orderId ? updated : o))
      );
    } catch {
      setError("Failed to update order status");
    } finally {
      setUpdatingId(null);
    }
  }

  async function handleExport() {
    try {
      await exportOrdersCsv();
    } catch {
      setError("Failed to export orders");
    }
  }

  if (user?.role !== "admin") {
    return null;
  }

  return (
    <section className="space-y-4 rounded-2xl bg-white p-6 shadow-md">
      <header className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold text-brand-primary">
            Orders overview
          </h2>
          <p className="text-xs text-brand-muted">
            Monitor status across printers and trigger notifications.
          </p>
        </div>
        <button
          onClick={handleExport}
          className="rounded-md border border-slate-200 px-4 py-2 text-xs font-semibold text-brand-primary hover:border-brand-accent"
        >
          Export CSV
        </button>
      </header>

      {error && <p className="text-sm text-red-500">{error}</p>}

      {isLoading ? (
        <p className="text-sm text-brand-muted">Loading orders...</p>
      ) : orders.length === 0 ? (
        <p className="text-sm text-brand-muted">No orders yet.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-3 py-2 text-left font-semibold uppercase tracking-wide text-xs text-brand-muted">
                  Order
                </th>
                <th className="px-3 py-2 text-left font-semibold uppercase tracking-wide text-xs text-brand-muted">
                  Items
                </th>
                <th className="px-3 py-2 text-left font-semibold uppercase tracking-wide text-xs text-brand-muted">
                  Total
                </th>
                <th className="px-3 py-2 text-left font-semibold uppercase tracking-wide text-xs text-brand-muted">
                  Created
                </th>
                <th className="px-3 py-2 text-left font-semibold uppercase tracking-wide text-xs text-brand-muted">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {orders.map((order) => (
                <tr key={order.id}>
                  <td className="px-3 py-2 font-medium text-brand-primary">
                    {order.order_number}
                  </td>
                  <td className="px-3 py-2">{order.items.length}</td>
                  <td className="px-3 py-2">€ {order.total_price.toFixed(2)}</td>
                  <td className="px-3 py-2">
                    {new Date(order.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-3 py-2">
                    <select
                      value={order.status}
                      onChange={(e) =>
                        handleStatusChange(order.id, e.target.value)
                      }
                      disabled={updatingId === order.id}
                      className={`rounded-full px-3 py-1 text-xs font-semibold ${
                        statusStyles[order.status] ?? "bg-slate-200 text-slate-700"
                      }`}
                    >
                      {statusOptions.map((s) => (
                        <option key={s} value={s}>
                          {s.replace(/_/g, " ")}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
