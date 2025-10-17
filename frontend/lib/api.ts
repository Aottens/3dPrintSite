import axios from "axios";

export interface Material {
  id: number;
  family: string;
  brand: string;
  color_name: string;
  hex: string;
  density: number;
  cost_per_kg: number;
  surcharge: number;
  active: boolean;
}

export interface QuotePayload {
  model_id: number;
  material_id: number;
  quantity: number;
  post_processing_minutes: number;
}

export interface QuoteResponse {
  quote_id: number;
  unit_price: number;
  total: number;
  lead_time_days: number;
  breakdown: Record<string, number>;
  config_version: string;
}

export interface PricingConfigResponse {
  version: string;
  effective_from: string;
  parameters: Record<string, unknown>;
  created_by: string;
}

const client = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
});

export async function fetchMaterials(): Promise<Material[]> {
  const { data } = await client.get<Material[]>("/api/materials");
  return data;
}

export async function uploadModel(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await client.post("/api/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data as { model_id: number } & Record<string, unknown>;
}

export async function requestQuote(payload: QuotePayload) {
  const { data } = await client.post<QuoteResponse>("/api/quote", payload);
  return data;
}

export async function fetchPricingConfig() {
  const { data } = await client.get<PricingConfigResponse>("/api/admin/pricing/config");
  return data;
}

export async function createMaterial(payload: Omit<Material, "id" | "active">) {
  const { data } = await client.post<Material>("/api/admin/material", payload);
  return data;
}
