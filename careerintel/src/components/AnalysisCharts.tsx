import { useMemo } from 'react';
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { getPath } from '../api/client';
import { SectionTitle } from './shared';

export function SkillComparisonChart({ rows }: { rows: Array<{ skill: string; current: number; required: number }> }) {
  return <section className="chart-surface"><SectionTitle title="Skill comparison" meta="Numeric values returned by the backend" /><div className="chart-wrap"><ResponsiveContainer width="100%" height={Math.max(210, rows.length * 42)}><BarChart data={rows} layout="vertical" margin={{ top: 6, right: 24, bottom: 4, left: 8 }}><CartesianGrid strokeDasharray="3 3" horizontal={false} /><XAxis type="number" domain={[0, 'dataMax']} tick={{ fill: '#77817f', fontSize: 11 }} axisLine={false} tickLine={false} /><YAxis type="category" dataKey="skill" width={110} tick={{ fill: '#34413f', fontSize: 12 }} axisLine={false} tickLine={false} /><Tooltip /><Legend /><Bar dataKey="current" name="Current" fill="#0B8F83" radius={[0, 5, 5, 0]} barSize={10} /><Bar dataKey="required" name="Required" fill="#bdc9c6" radius={[0, 5, 5, 0]} barSize={10} /></BarChart></ResponsiveContainer></div></section>;
}

export function DistributionChart({ title, data, labelPath, valuePath }: { title: string; data: unknown; labelPath?: string; valuePath?: string }) {
  const rows = useMemo(() => {
    if (Array.isArray(data)) {
      if (!labelPath || !valuePath) return [];
      return data.map((item) => ({ label: getPath(item, labelPath), value: getPath(item, valuePath) }))
        .filter((item): item is { label: string | number; value: number } => (typeof item.label === 'string' || typeof item.label === 'number') && typeof item.value === 'number')
        .slice(0, 24).map((item) => ({ label: String(item.label), value: item.value }));
    }
    if (data && typeof data === 'object') return Object.entries(data as Record<string, unknown>).filter(([, value]) => typeof value === 'number').slice(0, 24).map(([label, value]) => ({ label, value: value as number }));
    return [];
  }, [data]);
  if (!rows.length) return null;
  return <section className="surface chart-card"><SectionTitle title={title} meta="Backend-supplied series" /><div className="chart-wrap chart-small"><ResponsiveContainer width="100%" height={220}><BarChart data={rows} margin={{ top: 8, right: 16, bottom: 30, left: 4 }}><CartesianGrid strokeDasharray="3 3" vertical={false} /><XAxis dataKey="label" tick={{ fill: '#77817f', fontSize: 10 }} angle={-25} textAnchor="end" interval="preserveStartEnd" axisLine={false} tickLine={false} /><YAxis tick={{ fill: '#77817f', fontSize: 10 }} axisLine={false} tickLine={false} /><Tooltip /><Bar dataKey="value" name="Returned value" fill="#0B8F83" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer></div></section>;
}

export function RocCurveChart({ title, data, xPath, yPath, xLabel, yLabel }: { title: string; data: unknown; xPath?: string; yPath?: string; xLabel: string; yLabel: string }) {
  const points = useMemo(() => {
    if (!Array.isArray(data) || !xPath || !yPath) return [];
    return data.map((point) => ({ x: getPath(point, xPath), y: getPath(point, yPath) }))
      .filter((point): point is { x: number; y: number } => typeof point.x === 'number' && typeof point.y === 'number');
  }, [data, xPath, yPath]);
  if (!points.length) return null;
  return <section className="surface chart-card"><SectionTitle title={title} meta="Backend-supplied points · mapped axes" /><div className="chart-wrap chart-small"><ResponsiveContainer width="100%" height={240}><LineChart data={points} margin={{ top: 8, right: 16, bottom: 18, left: 5 }}><CartesianGrid strokeDasharray="3 3" /><XAxis type="number" dataKey="x" name={xLabel} label={{ value: xLabel, position: 'insideBottom', offset: -8 }} tick={{ fill: '#77817f', fontSize: 10 }} axisLine={false} tickLine={false} /><YAxis type="number" dataKey="y" name={yLabel} label={{ value: yLabel, angle: -90, position: 'insideLeft' }} tick={{ fill: '#77817f', fontSize: 10 }} axisLine={false} tickLine={false} /><Tooltip /><Line type="linear" dataKey="y" name={yLabel} stroke="#0B8F83" strokeWidth={2} dot={false} activeDot={{ r: 4 }} /></LineChart></ResponsiveContainer></div></section>;
}
