interface QuoteBreakdownProps {
  breakdown: Record<string, number> | null;
  leadTime?: number;
}

export function QuoteBreakdown({ breakdown, leadTime }: QuoteBreakdownProps) {
  if (!breakdown) {
    return (
      <p className="rounded-md border border-dashed border-brand-muted p-4 text-sm text-brand-muted">
        Upload a model and select options to receive an instant quote.
      </p>
    );
  }

  return (
    <div className="space-y-2 rounded-md border border-slate-200 bg-white p-4 shadow-sm">
      <h3 className="text-lg font-semibold text-brand-primary">Quote breakdown</h3>
      <dl className="grid grid-cols-2 gap-2 text-sm">
        {Object.entries(breakdown).map(([key, value]) => (
          <div key={key} className="flex items-center justify-between">
            <dt className="capitalize text-brand-muted">{key.replace(/_/g, " ")}</dt>
            <dd className="font-medium">€ {value.toFixed(2)}</dd>
          </div>
        ))}
      </dl>
      {typeof leadTime === "number" && (
        <p className="text-sm text-brand-muted">Estimated lead time: {leadTime} days</p>
      )}
    </div>
  );
}
