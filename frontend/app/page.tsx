import { UploadQuoteForm } from "../components/UploadQuoteForm";
import { PricingConfigPanel } from "../components/PricingConfigPanel";
import { OrdersOverview } from "../components/OrdersOverview";
import { CheckoutSummary } from "../components/CheckoutSummary";
import { AccountDashboard } from "../components/AccountDashboard";
import { AdminAnalytics } from "../components/AdminAnalytics";
import { UserManagementTable } from "../components/UserManagementTable";
import type { Material } from "../lib/api";

async function loadMaterials(): Promise<Material[]> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  try {
    const response = await fetch(`${apiUrl}/api/materials`, { next: { revalidate: 60 } });
    if (!response.ok) {
      throw new Error("Failed to fetch materials");
    }
    return (await response.json()) as Material[];
  } catch (error) {
    console.warn("Unable to fetch materials from API, falling back to defaults", error);
    return [
      {
        id: 1,
        family: "PLA",
        brand: "Generic",
        color_name: "Natural",
        hex: "#FFFFFF",
        density: 1.24,
        cost_per_kg: 45,
        surcharge: 0,
        active: true,
      },
    ];
  }
}

export default async function Home() {
  const materials = await loadMaterials();

  return (
    <div className="space-y-12">
      <UploadQuoteForm initialMaterials={materials} />
      <div className="grid gap-6 lg:grid-cols-[2fr,1fr]">
        <CheckoutSummary />
        <AccountDashboard />
      </div>
      <section id="admin" className="space-y-6">
        <AdminAnalytics />
        <PricingConfigPanel />
        <OrdersOverview />
        <UserManagementTable />
      </section>
    </div>
  );
}
