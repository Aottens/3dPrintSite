"use client";

import { useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import { QuoteBreakdown } from "./QuoteBreakdown";
import { fetchMaterials, requestQuote, uploadModel, type Material, type QuoteResponse } from "../lib/api";

interface UploadQuoteFormProps {
  initialMaterials: Material[];
}

export function UploadQuoteForm({ initialMaterials }: UploadQuoteFormProps) {
  const [materials, setMaterials] = useState<Material[]>(initialMaterials);
  const [selectedMaterial, setSelectedMaterial] = useState<number | null>(
    initialMaterials[0]?.id ?? null,
  );
  const [quantity, setQuantity] = useState(1);
  const [postMinutes, setPostMinutes] = useState(0);
  const [modelId, setModelId] = useState<number | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [quote, setQuote] = useState<QuoteResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refreshMaterials() {
    const data = await fetchMaterials();
    setMaterials(data);
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    setError(null);
    try {
      const response = await uploadModel(file);
      setModelId(response.model_id);
      setFileName(file.name);
      await refreshMaterials();
    } catch (err) {
      console.error(err);
      setError("Failed to upload model. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }

  async function handleQuoteRequest() {
    if (!modelId || !selectedMaterial) {
      setError("Upload a model and select a material first.");
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      const data = await requestQuote({
        model_id: modelId,
        material_id: selectedMaterial,
        quantity,
        post_processing_minutes: postMinutes,
      });
      setQuote(data);
    } catch (err) {
      console.error(err);
      setError("Unable to calculate quote. Check your inputs.");
    } finally {
      setIsLoading(false);
    }
  }

  const summary = useMemo(() => {
    if (!quote) return null;
    return {
      ...quote.breakdown,
      total: quote.total,
    };
  }, [quote]);

  return (
    <section id="customer" className="rounded-2xl bg-white p-6 shadow-md">
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold text-brand-primary">Upload &amp; Quote</h2>
          <p className="text-sm text-brand-muted">
            Drag-and-drop STL files, choose material parameters, and generate live pricing.
          </p>

          <label
            className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-brand-muted hover:border-brand-accent hover:text-brand-accent"
          >
            <span className="font-medium text-brand-primary">Upload STL file</span>
            <input type="file" accept=".stl" className="hidden" onChange={handleFileChange} />
            {fileName && <span className="mt-2 text-xs">Selected: {fileName}</span>}
          </label>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold uppercase text-brand-muted">Material</label>
              <select
                className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                value={selectedMaterial ?? undefined}
                onChange={(event) => setSelectedMaterial(Number(event.target.value))}
              >
                <option value="" disabled>
                  Select material
                </option>
                {materials.map((material) => (
                  <option key={material.id} value={material.id}>
                    {material.family} · {material.color_name}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold uppercase text-brand-muted">Quantity</label>
              <input
                type="number"
                min={1}
                value={quantity}
                onChange={(event) => setQuantity(Number(event.target.value))}
                className="rounded-md border border-slate-200 px-3 py-2 text-sm"
              />
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold uppercase text-brand-muted">Post-processing (min)</label>
              <input
                type="number"
                min={0}
                value={postMinutes}
                onChange={(event) => setPostMinutes(Number(event.target.value))}
                className="rounded-md border border-slate-200 px-3 py-2 text-sm"
              />
            </div>
          </div>

          <button
            onClick={handleQuoteRequest}
            className="rounded-md bg-brand-accent px-4 py-2 text-sm font-semibold text-white shadow hover:bg-emerald-500"
            disabled={isLoading}
          >
            {isLoading ? "Calculating..." : "Get instant quote"}
          </button>

          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>

        <div className="space-y-4">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
            <h3 className="text-lg font-semibold text-brand-primary">Model viewer</h3>
            <p className="text-sm text-brand-muted">
              Preview models in 3D. Integrate your preferred viewer (e.g. react-three-fiber) here.
            </p>
          </div>
          <QuoteBreakdown breakdown={summary} leadTime={quote?.lead_time_days} />
        </div>
      </div>
    </section>
  );
}
