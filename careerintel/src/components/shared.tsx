import type { ReactNode } from 'react';
import { AlertCircle, ArrowUpRight, CircleHelp, Database, LoaderCircle, RotateCw } from 'lucide-react';
import type { Capability } from '../types';
import { useApp } from '../app/AppContext';

export function PageHeading({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) {
  return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action && <div className="page-heading-action">{action}</div>}</div>;
}

export function SectionTitle({ title, meta, children }: { title: string; meta?: string; children?: ReactNode }) {
  return <div className="section-title"><div><h2>{title}</h2>{meta && <span>{meta}</span>}</div>{children}</div>;
}

export function MetricCard({ label, value, detail, tone = 'neutral', icon }: { label: string; value: unknown; detail?: string; tone?: 'neutral' | 'positive' | 'warning' | 'accent'; icon?: ReactNode }) {
  const valid = value !== undefined && value !== null && value !== '';
  return <article className={`metric-card metric-${tone}`}>
    <div className="metric-top"><span>{label}</span>{icon && <span className="metric-icon">{icon}</span>}</div>
    <div className={`metric-value ${!valid ? 'metric-missing' : ''}`}>{valid ? String(value) : 'Not returned'}</div>
    {detail && <div className="metric-detail">{detail}</div>}
  </article>;
}

export function EmptyState({ title, detail, action, icon = <Database size={19} /> }: { title: string; detail: string; action?: ReactNode; icon?: ReactNode }) {
  return <div className="empty-state"><span className="empty-icon">{icon}</span><div><h3>{title}</h3><p>{detail}</p>{action && <div className="empty-action">{action}</div>}</div></div>;
}

export function LoadingState({ label = 'Loading backend analysis…' }: { label?: string }) {
  return <div className="loading-state"><LoaderCircle className="spin" size={19} /><span>{label}</span></div>;
}

export function ErrorState({ title = 'Analysis could not be loaded', message, retry }: { title?: string; message: string; retry: () => void }) {
  return <div className="error-state"><AlertCircle size={19} /><div><strong>{title}</strong><p>{message}</p><button className="button button-quiet" onClick={retry}><RotateCw size={14} /> Retry</button></div></div>;
}

export function JsonResponse({ capability, compact = false }: { capability: Capability; compact?: boolean }) {
  const { results, states } = useApp();
  const result = results[capability];
  if (!result || states[capability] !== 'loaded') return null;
  return <details className={`response-viewer ${compact ? 'response-compact' : ''}`}>
    <summary><span><CircleHelp size={14} /> Raw response</span><span className="muted-inline">{result.operationId || 'backend response'} <ArrowUpRight size={12} /></span></summary>
    <pre>{JSON.stringify(result.value, null, 2)}</pre>
  </details>;
}

export function CapabilityPanel({ capability, title, description, children, className = '' }: { capability: Capability; title?: string; description?: string; children?: ReactNode; className?: string }) {
  const { runCapability, states, errors, results } = useApp();
  const state = states[capability];
  const run = () => void runCapability(capability).catch(() => undefined);
  return <section className={`surface capability-panel ${className}`}>
    {(title || description) && <SectionTitle title={title || 'Backend output'} meta={description}>
      <button className="button button-primary button-small" onClick={run} disabled={state === 'loading'}>{state === 'loading' ? <LoaderCircle className="spin" size={14} /> : <RotateCw size={14} />}{state === 'loaded' ? 'Refresh' : 'Load from backend'}</button>
    </SectionTitle>}
    {state === 'loading' && <LoadingState />}
    {state === 'error' && <ErrorState message={errors[capability] || 'Request failed.'} retry={run} />}
    {state !== 'loading' && state !== 'error' && children}
    {results[capability] && state === 'loaded' && <div className="provenance"><span className="provenance-dot" /> Backend response · {new Date(results[capability]!.receivedAt).toLocaleString()}</div>}
    <JsonResponse capability={capability} compact />
  </section>;
}

export function DataPills({ items }: { items: unknown[] }) {
  if (!items.length) return <div className="muted-note">No items returned by the backend.</div>;
  return <div className="data-pills">{items.map((item, index) => <span key={index}>{typeof item === 'string' || typeof item === 'number' ? String(item) : JSON.stringify(item)}</span>)}</div>;
}

export function RecordList({ rows, label }: { rows: unknown[]; label: (row: unknown, index: number) => string }) {
  if (!rows.length) return <EmptyState title="No records returned" detail="The backend response did not include any records for this request." />;
  return <div className="record-list">{rows.map((row, index) => <div className="record-row" key={index}><span className="record-index">{String(index + 1).padStart(2, '0')}</span><span>{label(row, index)}</span><code>{typeof row === 'object' && row ? Object.keys(row).length : typeof row} fields</code></div>)}</div>;
}
