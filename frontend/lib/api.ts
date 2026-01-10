import axios from "axios";

// API client configuration
const client = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
});

// Add auth token to requests
client.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle auth errors
client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("token");
        localStorage.removeItem("user");
      }
    }
    return Promise.reject(error);
  }
);

// Types
export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  company_name: string | null;
  is_active: boolean;
}

export interface MaterialColor {
  id: number;
  name: string;
  hex_code: string;
  is_active: boolean;
}

export interface Material {
  id: number;
  category_id: number;
  category_name: string;
  technology: string;
  name: string;
  brand: string;
  density_g_cm3: number;
  cost_per_kg: number;
  surcharge: number;
  is_active: boolean;
  colors: MaterialColor[];
}

export interface PrintProfile {
  id: number;
  technology: string;
  name: string;
  layer_height_mm: number;
  infill_percentage: number;
  supports_enabled: boolean;
  quality_multiplier: number;
  speed_multiplier: number;
  description: string | null;
  is_active: boolean;
}

export interface ModelFile {
  id: string;
  original_filename: string;
  file_size_bytes: number;
  metrics_status: string;
  volume_cm3: number | null;
  surface_area_cm2: number | null;
  bounding_box_mm: { x: number; y: number; z: number } | null;
  is_manifold: boolean | null;
  is_watertight: boolean | null;
  metrics_error: string | null;
  created_at: string;
}

export interface PriceBreakdown {
  material_cost: number;
  machine_cost: number;
  handling_fee: number;
  support_cost: number;
  quality_multiplier: number;
  risk_multiplier: number;
  subtotal: number;
  minimum_applied: boolean;
  unit_price: number;
  total_price: number;
}

export interface Quote {
  id: string;
  model_file_id: string;
  material_id: number;
  material_name: string;
  color_id: number;
  color_name: string;
  profile_id: number;
  profile_name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  lead_time_days: number;
  breakdown: PriceBreakdown;
  pricing_version: string;
  is_valid: boolean;
  expires_at: string;
  created_at: string;
}

export interface OrderItem {
  id: number;
  quote_id: string;
  status: string;
  printer_assigned: string | null;
  model_filename: string;
  material_name: string;
  color_name: string;
  quantity: number;
  unit_price: number;
}

export interface Order {
  id: string;
  order_number: string;
  user_id: string;
  status: string;
  shipping_address: Record<string, string>;
  tracking_code: string | null;
  subtotal: number;
  shipping_cost: number;
  total_price: number;
  has_price_override: boolean;
  override_price: number | null;
  override_reason: string | null;
  notes: string | null;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
}

export interface OrderListItem {
  id: string;
  order_number: string;
  status: string;
  total_price: number;
  item_count: number;
  created_at: string;
}

export interface PricingRuleSet {
  id: number;
  version: string;
  name: string;
  effective_from: string;
  effective_to: string | null;
  parameters: Record<string, unknown>;
  is_active: boolean;
  created_by: string;
  created_at: string;
}

export interface AnalyticsSummary {
  orders_7d: number;
  revenue_7d: number;
  top_material: string;
  top_material_orders: number;
  avg_lead_time_days: number;
}

// Auth API
export async function login(email: string, password: string): Promise<{ token: string; user: User }> {
  const { data } = await client.post("/api/auth/login", { email, password });
  const token = data.access_token;

  // Get user info
  const userResponse = await axios.get(`${client.defaults.baseURL}/api/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  return { token, user: userResponse.data };
}

export async function register(email: string, name: string, password: string, company_name?: string): Promise<User> {
  const { data } = await client.post("/api/auth/register", {
    email,
    name,
    password,
    company_name,
  });
  return data;
}

export async function getCurrentUser(): Promise<User> {
  const { data } = await client.get("/api/auth/me");
  return data;
}

// Materials API
export async function fetchTechnologies(): Promise<{ id: string; name: string; description: string }[]> {
  const { data } = await client.get("/api/technologies");
  return data;
}

export async function fetchMaterials(technology?: string): Promise<Material[]> {
  const params = technology ? { technology } : {};
  const { data } = await client.get<Material[]>("/api/materials", { params });
  return data;
}

export async function fetchMaterial(id: number): Promise<Material> {
  const { data } = await client.get<Material>(`/api/materials/${id}`);
  return data;
}

export async function fetchProfiles(technology?: string): Promise<PrintProfile[]> {
  const params = technology ? { technology } : {};
  const { data } = await client.get<PrintProfile[]>("/api/profiles", { params });
  return data;
}

// Assets API
export async function uploadModel(file: File): Promise<ModelFile> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await client.post<ModelFile>("/api/assets/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function getAsset(id: string): Promise<ModelFile> {
  const { data } = await client.get<ModelFile>(`/api/assets/${id}`);
  return data;
}

export async function getAssetDownloadUrl(id: string): Promise<string> {
  return `${client.defaults.baseURL}/api/assets/${id}/download`;
}

// Quotes API
export async function createQuote(
  model_file_id: string,
  material_id: number,
  color_id: number,
  profile_id: number,
  quantity: number = 1
): Promise<Quote> {
  const { data } = await client.post<Quote>("/api/quotes", {
    model_file_id,
    material_id,
    color_id,
    profile_id,
    quantity,
  });
  return data;
}

export async function fetchQuotes(valid_only?: boolean): Promise<Quote[]> {
  const params = valid_only !== undefined ? { valid_only } : {};
  const { data } = await client.get<Quote[]>("/api/quotes", { params });
  return data;
}

export async function fetchQuote(id: string): Promise<Quote> {
  const { data } = await client.get<Quote>(`/api/quotes/${id}`);
  return data;
}

// Orders API
export async function createOrder(
  quote_ids: string[],
  shipping_address: {
    street: string;
    city: string;
    postal_code: string;
    country: string;
    company_name?: string;
  }
): Promise<Order> {
  const { data } = await client.post<Order>("/api/orders", {
    quote_ids,
    shipping_address,
  });
  return data;
}

export async function fetchOrders(status?: string): Promise<OrderListItem[]> {
  const params = status ? { status } : {};
  const { data } = await client.get<OrderListItem[]>("/api/orders", { params });
  return data;
}

export async function fetchOrder(id: string): Promise<Order> {
  const { data } = await client.get<Order>(`/api/orders/${id}`);
  return data;
}

// Admin API
export async function fetchPricingConfig(): Promise<PricingRuleSet> {
  const { data } = await client.get<PricingRuleSet>("/api/admin/pricing/current");
  return data;
}

export async function fetchAllPricingConfigs(): Promise<PricingRuleSet[]> {
  const { data } = await client.get<PricingRuleSet[]>("/api/admin/pricing");
  return data;
}

export async function createPricingConfig(
  version: string,
  name: string,
  effective_from: string,
  parameters: Record<string, unknown>
): Promise<PricingRuleSet> {
  const { data } = await client.post<PricingRuleSet>("/api/admin/pricing", {
    version,
    name,
    effective_from,
    parameters,
  });
  return data;
}

export async function fetchAllOrders(status?: string): Promise<Order[]> {
  const params = status ? { status } : {};
  const { data } = await client.get<Order[]>("/api/admin/orders", { params });
  return data;
}

export async function updateOrderStatus(
  orderId: string,
  status: string,
  tracking_code?: string,
  notes?: string
): Promise<Order> {
  const { data } = await client.patch<Order>(`/api/admin/orders/${orderId}/status`, {
    status,
    tracking_code,
    notes,
  });
  return data;
}

export async function overrideOrderPrice(
  orderId: string,
  override_price: number,
  reason: string
): Promise<Order> {
  const { data } = await client.post<Order>(`/api/admin/orders/${orderId}/override-price`, {
    override_price,
    reason,
  });
  return data;
}

export async function fetchAnalytics(): Promise<AnalyticsSummary> {
  const { data } = await client.get<AnalyticsSummary>("/api/admin/analytics/summary");
  return data;
}

export async function fetchUsers(): Promise<User[]> {
  const { data } = await client.get<User[]>("/api/admin/users");
  return data;
}

export async function toggleUserActive(userId: string): Promise<{ id: string; is_active: boolean }> {
  const { data } = await client.patch(`/api/admin/users/${userId}/toggle-active`);
  return data;
}

export async function createMaterial(
  category_id: number,
  name: string,
  brand: string,
  density_g_cm3: number,
  cost_per_kg: number,
  surcharge?: number
): Promise<Material> {
  const { data } = await client.post<Material>("/api/admin/materials", {
    category_id,
    name,
    brand,
    density_g_cm3,
    cost_per_kg,
    surcharge: surcharge ?? 0,
  });
  return data;
}

export async function updateMaterial(
  id: number,
  updates: Partial<{
    name: string;
    brand: string;
    density_g_cm3: number;
    cost_per_kg: number;
    surcharge: number;
    is_active: boolean;
  }>
): Promise<Material> {
  const { data } = await client.put<Material>(`/api/admin/materials/${id}`, updates);
  return data;
}

export async function exportOrdersCsv(): Promise<void> {
  const response = await client.get("/api/admin/orders/export/csv", {
    responseType: "blob",
  });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", `orders_${new Date().toISOString().split("T")[0]}.csv`);
  document.body.appendChild(link);
  link.click();
  link.remove();
}

export default client;
