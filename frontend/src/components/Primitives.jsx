import React from "react";

export function Panel({ title, subtitle, right, children, className = "", testId, noPad = false }) {
  return (
    <section data-testid={testId} className={`pp-surface rounded-lg ${className}`}>
      {(title || right) && (
        <header className="flex items-center justify-between border-b border-[#282E3A] px-4 py-3">
          <div>
            {title && <h3 className="text-sm font-semibold text-[#E2E8F0]">{title}</h3>}
            {subtitle && <p className="mt-0.5 text-xs text-[#64748B]">{subtitle}</p>}
          </div>
          {right}
        </header>
      )}
      <div className={noPad ? "" : "p-4"}>{children}</div>
    </section>
  );
}

export function PageHeader({ title, description, actions, testId }) {
  return (
    <div data-testid={testId} className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[#E2E8F0]">{title}</h1>
        {description && <p className="mt-1 max-w-2xl text-sm text-[#94A3B8]">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Stat({ label, value, sub, accent = "#38BDF8", icon: Icon, testId }) {
  return (
    <div data-testid={testId} className="pp-surface rounded-lg p-4">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-[#64748B]">{label}</span>
        {Icon && <Icon size={16} style={{ color: accent }} />}
      </div>
      <div className="mt-2 font-mono text-2xl font-semibold text-[#E2E8F0]">{value}</div>
      {sub && <div className="mt-1 text-xs text-[#64748B]">{sub}</div>}
    </div>
  );
}

export function EmptyState({ icon: Icon, title, description, action, testId }) {
  return (
    <div data-testid={testId} className="flex flex-col items-center justify-center rounded-lg border border-dashed border-[#282E3A] bg-[#14171D]/40 px-6 py-14 text-center">
      {Icon && (
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg border border-[#282E3A] bg-[#1C2028]">
          <Icon size={22} className="text-[#64748B]" />
        </div>
      )}
      <h3 className="text-sm font-semibold text-[#E2E8F0]">{title}</h3>
      {description && <p className="mt-1 max-w-sm text-sm text-[#64748B]">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}

export function Field({ label, hint, children, mono = false }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-xs font-medium text-[#94A3B8]">{label}</span>
      {children}
      {hint && <span className={`mt-1 block text-xs text-[#64748B] ${mono ? "font-mono" : ""}`}>{hint}</span>}
    </label>
  );
}

export function Mono({ children, className = "" }) {
  return <span className={`font-mono ${className}`}>{children}</span>;
}
