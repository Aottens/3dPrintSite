"use client";

import { useEffect, useMemo, useState } from "react";
import type { ChangeEvent } from "react";
import dynamic from "next/dynamic";
import { QuoteBreakdown } from "./QuoteBreakdown";
import {
  fetchMaterials,
  fetchProfiles,
  fetchTechnologies,
  uploadModel,
  createQuote,
  getAsset,
  type Material,
  type PrintProfile,
  type Quote,
  type ModelFile,
} from "../lib/api";
import { useAuthStore } from "../lib/store";
import { useCartStore } from "../lib/store";

// Dynamic import for 3D viewer (client-side only)
const ModelViewer = dynamic(() => import("./ModelViewer"), {
  ssr: false,
  loading: () => (
    <div className="h-64 flex items-center justify-center bg-slate-100 rounded-lg">
      <p className="text-sm text-brand-muted">Loading 3D viewer...</p>
    </div>
  ),
});

interface UploadQuoteFormProps {
  initialMaterials?: Material[];
}

export function UploadQuoteForm({ initialMaterials = [] }: UploadQuoteFormProps) {
  const { isAuthenticated } = useAuthStore();
  const { addItem } = useCartStore();

  // Technologies and materials
  const [technologies, setTechnologies] = useState<{ id: string; name: string }[]>([]);
  const [selectedTechnology, setSelectedTechnology] = useState<string>("fdm");
  const [materials, setMaterials] = useState<Material[]>(initialMaterials);
  const [profiles, setProfiles] = useState<PrintProfile[]>([]);

  // Selected options
  const [selectedMaterial, setSelectedMaterial] = useState<number | null>(null);
  const [selectedColor, setSelectedColor] = useState<number | null>(null);
  const [selectedProfile, setSelectedProfile] = useState<number | null>(null);
  const [quantity, setQuantity] = useState(1);

  // Model state
  const [modelFile, setModelFile] = useState<ModelFile | null>(null);
  const [modelBlob, setModelBlob] = useState<Blob | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);

  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [isCalculating, setIsCalculating] = useState(false);
  const [quote, setQuote] = useState<Quote | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [metricsPolling, setMetricsPolling] = useState(false);

  // Load technologies on mount
  useEffect(() => {
    fetchTechnologies()
      .then(setTechnologies)
      .catch(() => {
        setTechnologies([
          { id: "fdm", name: "FDM" },
          { id: "resin", name: "Resin" },
        ]);
      });
  }, []);

  // Load materials when technology changes
  useEffect(() => {
    fetchMaterials(selectedTechnology)
      .then((data) => {
        setMaterials(data);
        if (data.length > 0) {
          setSelectedMaterial(data[0].id);
          if (data[0].colors.length > 0) {
            setSelectedColor(data[0].colors[0].id);
          }
        }
      })
      .catch(console.error);

    fetchProfiles(selectedTechnology)
      .then((data) => {
        setProfiles(data);
        if (data.length > 0) {
          setSelectedProfile(data[0].id);
        }
      })
      .catch(console.error);
  }, [selectedTechnology]);

  // Poll for metrics completion
  useEffect(() => {
    if (!modelFile || !metricsPolling) return;

    if (modelFile.metrics_status === "completed") {
      setMetricsPolling(false);
      return;
    }

    if (modelFile.metrics_status === "failed") {
      setError(`Metrics calculation failed: ${modelFile.metrics_error}`);
      setMetricsPolling(false);
      return;
    }

    const interval = setInterval(async () => {
      try {
        const updated = await getAsset(modelFile.id);
        setModelFile(updated);

        if (updated.metrics_status === "completed" || updated.metrics_status === "failed") {
          setMetricsPolling(false);
        }
      } catch {
        // Ignore polling errors
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [modelFile, metricsPolling]);

  // Get current material's colors
  const currentMaterial = materials.find((m) => m.id === selectedMaterial);
  const availableColors = currentMaterial?.colors.filter((c) => c.is_active) ?? [];

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;

    // Validate file type
    const validExtensions = [".stl", ".3mf"];
    const ext = file.name.toLowerCase().substring(file.name.lastIndexOf("."));
    if (!validExtensions.includes(ext)) {
      setError(`Invalid file type. Supported formats: ${validExtensions.join(", ")}`);
      return;
    }

    // Validate file size (200MB max)
    if (file.size > 200 * 1024 * 1024) {
      setError("File too large. Maximum size: 200MB");
      return;
    }

    if (!isAuthenticated) {
      setError("Please log in to upload files");
      return;
    }

    setIsLoading(true);
    setError(null);
    setQuote(null);

    try {
      // Store blob for preview
      setModelBlob(file);
      setFileName(file.name);

      // Upload to server
      const response = await uploadModel(file);
      setModelFile(response);

      // Start polling for metrics
      if (response.metrics_status === "pending" || response.metrics_status === "processing") {
        setMetricsPolling(true);
      }
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to upload model. Please try again.");
      setModelBlob(null);
      setFileName(null);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleQuoteRequest() {
    if (!modelFile) {
      setError("Please upload a model first");
      return;
    }

    if (!selectedMaterial || !selectedColor || !selectedProfile) {
      setError("Please select material, color, and print profile");
      return;
    }

    if (modelFile.metrics_status !== "completed") {
      setError("Model metrics are still being calculated. Please wait.");
      return;
    }

    setIsCalculating(true);
    setError(null);

    try {
      const data = await createQuote(
        modelFile.id,
        selectedMaterial,
        selectedColor,
        selectedProfile,
        quantity
      );
      setQuote(data);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Unable to calculate quote. Please try again.");
    } finally {
      setIsCalculating(false);
    }
  }

  function handleAddToCart() {
    if (quote) {
      addItem(quote);
      // Reset for next quote
      setQuote(null);
      setModelFile(null);
      setModelBlob(null);
      setFileName(null);
    }
  }

  const metricsDisplay = useMemo(() => {
    if (!modelFile) return null;

    if (modelFile.metrics_status === "pending" || modelFile.metrics_status === "processing") {
      return (
        <div className="text-sm text-amber-600 animate-pulse">
          Calculating model metrics...
        </div>
      );
    }

    if (modelFile.metrics_status === "failed") {
      return (
        <div className="text-sm text-red-500">
          Failed: {modelFile.metrics_error}
        </div>
      );
    }

    if (modelFile.metrics_status === "completed" && modelFile.volume_cm3) {
      return (
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div>
            <span className="text-brand-muted">Volume:</span>{" "}
            <span className="font-medium">{modelFile.volume_cm3.toFixed(2)} cm³</span>
          </div>
          {modelFile.surface_area_cm2 && (
            <div>
              <span className="text-brand-muted">Surface:</span>{" "}
              <span className="font-medium">{modelFile.surface_area_cm2.toFixed(2)} cm²</span>
            </div>
          )}
          {modelFile.bounding_box_mm && (
            <div className="col-span-2">
              <span className="text-brand-muted">Size:</span>{" "}
              <span className="font-medium">
                {modelFile.bounding_box_mm.x.toFixed(1)} x{" "}
                {modelFile.bounding_box_mm.y.toFixed(1)} x{" "}
                {modelFile.bounding_box_mm.z.toFixed(1)} mm
              </span>
            </div>
          )}
          <div className="col-span-2 flex gap-2">
            {modelFile.is_watertight && (
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                Watertight
              </span>
            )}
            {modelFile.is_manifold && (
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">
                Manifold
              </span>
            )}
            {!modelFile.is_watertight && (
              <span className="text-xs bg-amber-100 text-amber-700 px-2 py-1 rounded">
                Non-watertight
              </span>
            )}
          </div>
        </div>
      );
    }

    return null;
  }, [modelFile]);

  const breakdown = useMemo(() => {
    if (!quote) return null;
    return {
      material: quote.breakdown.material_cost,
      machine: quote.breakdown.machine_cost,
      handling: quote.breakdown.handling_fee,
      support: quote.breakdown.support_cost,
      total: quote.total_price,
    };
  }, [quote]);

  return (
    <section id="customer" className="rounded-2xl bg-white p-6 shadow-md">
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4">
          <h2 className="text-2xl font-semibold text-brand-primary">Upload &amp; Quote</h2>
          <p className="text-sm text-brand-muted">
            Upload STL or 3MF files, choose material and print settings, and get instant pricing.
          </p>

          {!isAuthenticated && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-md text-sm text-amber-800">
              Please log in to upload files and get quotes.
            </div>
          )}

          <label
            className="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-brand-muted hover:border-brand-accent hover:text-brand-accent"
          >
            <span className="font-medium text-brand-primary">
              {isLoading ? "Uploading..." : "Upload STL or 3MF file"}
            </span>
            <input
              type="file"
              accept=".stl,.3mf"
              className="hidden"
              onChange={handleFileChange}
              disabled={isLoading || !isAuthenticated}
            />
            {fileName && (
              <span className="mt-2 text-xs text-brand-primary">
                Selected: {fileName}
              </span>
            )}
          </label>

          {metricsDisplay && (
            <div className="p-3 bg-slate-50 rounded-md border border-slate-200">
              {metricsDisplay}
            </div>
          )}

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold uppercase text-brand-muted">
                Technology
              </label>
              <select
                className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                value={selectedTechnology}
                onChange={(e) => setSelectedTechnology(e.target.value)}
              >
                {technologies.map((tech) => (
                  <option key={tech.id} value={tech.id}>
                    {tech.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold uppercase text-brand-muted">
                Material
              </label>
              <select
                className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                value={selectedMaterial ?? ""}
                onChange={(e) => {
                  const matId = Number(e.target.value);
                  setSelectedMaterial(matId);
                  const mat = materials.find((m) => m.id === matId);
                  if (mat?.colors.length) {
                    setSelectedColor(mat.colors[0].id);
                  }
                }}
              >
                <option value="" disabled>
                  Select material
                </option>
                {materials.map((material) => (
                  <option key={material.id} value={material.id}>
                    {material.category_name} - {material.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold uppercase text-brand-muted">
                Color
              </label>
              <select
                className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                value={selectedColor ?? ""}
                onChange={(e) => setSelectedColor(Number(e.target.value))}
                disabled={availableColors.length === 0}
              >
                <option value="" disabled>
                  Select color
                </option>
                {availableColors.map((color) => (
                  <option key={color.id} value={color.id}>
                    {color.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold uppercase text-brand-muted">
                Print Profile
              </label>
              <select
                className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                value={selectedProfile ?? ""}
                onChange={(e) => setSelectedProfile(Number(e.target.value))}
              >
                <option value="" disabled>
                  Select profile
                </option>
                {profiles.map((profile) => (
                  <option key={profile.id} value={profile.id}>
                    {profile.name}
                    {profile.supports_enabled ? " (with supports)" : ""}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-xs font-semibold uppercase text-brand-muted">
                Quantity
              </label>
              <input
                type="number"
                min={1}
                value={quantity}
                onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
                className="rounded-md border border-slate-200 px-3 py-2 text-sm"
              />
            </div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleQuoteRequest}
              className="rounded-md bg-brand-accent px-4 py-2 text-sm font-semibold text-white shadow hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={
                isLoading ||
                isCalculating ||
                !modelFile ||
                modelFile.metrics_status !== "completed" ||
                !isAuthenticated
              }
            >
              {isCalculating ? "Calculating..." : "Get instant quote"}
            </button>

            {quote && (
              <button
                onClick={handleAddToCart}
                className="rounded-md border border-brand-accent px-4 py-2 text-sm font-semibold text-brand-accent hover:bg-emerald-50"
              >
                Add to cart
              </button>
            )}
          </div>

          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>

        <div className="space-y-4">
          <div className="rounded-lg border border-slate-200 bg-slate-50 overflow-hidden">
            <h3 className="px-4 pt-4 text-lg font-semibold text-brand-primary">
              Model Preview
            </h3>
            {modelBlob ? (
              <ModelViewer fileBlob={modelBlob} className="h-64" />
            ) : (
              <div className="h-64 flex items-center justify-center">
                <p className="text-sm text-brand-muted">
                  Upload a model to see preview
                </p>
              </div>
            )}
          </div>

          <QuoteBreakdown breakdown={breakdown} leadTime={quote?.lead_time_days} />
        </div>
      </div>
    </section>
  );
}
