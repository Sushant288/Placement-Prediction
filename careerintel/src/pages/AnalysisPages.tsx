import { lazy, Suspense, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Activity, ArrowDownRight, ArrowUpRight, BookOpenCheck, ChevronRight, CircleHelp, Database, Gauge, GraduationCap, Info, Lightbulb, RefreshCw, ShieldAlert, Sparkles, Target, TrendingUp, UserRound } from 'lucide-react';
import { useApp } from '../app/AppContext';
import { getPath } from '../api/client';
import { CapabilityPanel, DataPills, EmptyState, MetricCard, PageHeading, SectionTitle } from '../components/shared';
import SchemaForm from '../components/SchemaForm';
import type { Capability } from '../types';

const SkillComparisonChart = lazy(() => import('../components/AnalysisCharts').then((module) => ({ default: module.SkillComparisonChart })));
const DistributionChart = lazy(() => import('../components/AnalysisCharts').then((module) => ({ default: module.DistributionChart })));
const RocCurveChart = lazy(() => import('../components/AnalysisCharts').then((module) => ({ default: module.RocCurveChart })));

type PageKey = 'overview' | 'profile' | 'placement' | 'skills' | 'recommendations' | 'whatIf' | 'salary' | 'eda' | 'models';
const labels: Record<string, string> = {
  probability: 'Placement probability', prediction: 'Prediction', readiness: 'Readiness score', risk: 'Risk interpretation',
  confidence: 'Model confidence', model: 'Model used', generatedAt: 'Generated at', roleFit: 'Role fit', salary: 'Salary/package',
  low: 'Lower range', high: 'Upper range', currency: 'Currency', originalProbability: 'Original probability',
  updatedProbability: 'Updated probability', difference: 'Difference', records: 'Dataset records', features: 'Dataset features',
  missingValues: 'Missing values', dataTypes: 'Data types', classification: 'Classification results', regression: 'Regression results',
  comparison: 'Model comparison', confusionMatrix: 'Confusion matrix', roc: 'ROC curve', calibration: 'Calibration',
  featureImportance: 'Feature importance', explanation: 'Interpretation', expectedImpact: 'Expected impact',
};
const capabilityCopy: Record<Capability, { title: string; description: string }> = {
  students: { title: 'Student directory', description: 'Load records returned by the configured student-list operation.' },
  createStudent: { title: 'Student profile creation', description: 'Create a profile using documented request fields.' },
  profile: { title: 'Student profile from backend', description: 'Profile for the currently selected student.' },
  placement: { title: 'Placement prediction', description: 'The model’s response for the current student profile.' },
  roles: { title: 'Available target roles', description: 'Roles returned by the backend requirements catalog.' },
  skillGap: { title: 'Role fit and skill comparison', description: 'Current values and role requirements returned by the configured analysis.' },
  recommendations: { title: 'Recommendations from the engine', description: 'Student-specific recommendations returned by the backend.' },
  whatIf: { title: 'What-if model result', description: 'Recalculation returned by the existing backend/model.' },
  salary: { title: 'Salary prediction', description: 'Show only a valid prediction returned for this student.' },
  eda: { title: 'Dataset analysis', description: 'Actual EDA results from the project dataset.' },
  models: { title: 'Model evaluation artifacts', description: 'Evaluation results and model artifacts returned by the project.' },
};

function display(value: unknown): string {
  if (value === undefined || value === null || value === '') return 'Not returned';
  if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') return String(value);
  return JSON.stringify(value);
}
function present(value: unknown) { return value !== undefined && value !== null && value !== ''; }
function objectEntries(value: unknown): Array<[string, unknown]> {
  return value && typeof value === 'object' && !Array.isArray(value) ? Object.entries(value as Record<string, unknown>) : [];
}
function useMetrics(capability: Capability, keys: string[]) {
  const { mapped, settings } = useApp();
  return keys.map((key) => ({ key, label: labels[key] || key, value: mapped(capability, key), configured: Boolean(settings.bindings[capability].fieldPaths[key]) }))
    .filter((item) => item.configured || present(item.value));
}

function MappedMetrics({ capability, keys, tone = 'neutral' }: { capability: Capability; keys: string[]; tone?: 'neutral' | 'positive' | 'warning' | 'accent' }) {
  const fields = useMetrics(capability, keys);
  if (!fields.length) return <EmptyState title="No named fields mapped" detail="Connect this backend operation and map the response fields in Backend connection. The raw response remains available when returned." />;
  return <div className="metric-grid">{fields.map((item) => <MetricCard key={item.key} label={item.label} value={item.value} tone={tone} />)}</div>;
}

function MappedData({ capability, keys }: { capability: Capability; keys: string[] }) {
  const { mapped, settings } = useApp();
  const fields = keys.map((key) => ({ key, value: mapped(capability, key), configured: Boolean(settings.bindings[capability].fieldPaths[key]) }))
    .filter((item) => item.configured || present(item.value));
  if (!fields.length) return <EmptyState title="No mapped output fields" detail="Map the relevant keys to paths from the backend response. No value is inferred or filled in by the frontend." />;
  return <div className="mapped-data-grid">{fields.map(({ key, value }) => <article key={key} className="mapped-data-card"><div className="mapped-data-label">{labels[key] || key}</div>{Array.isArray(value) ? <DataPills items={value} /> : <div className="mapped-data-value">{display(value)}</div>}</article>)}</div>;
}

function StudentRequired({ title = 'Select a student to begin', detail = 'Choose a real student record returned by your backend in the header.' }: { title?: string; detail?: string }) {
  return <EmptyState title={title} detail={detail} icon={<GraduationCap size={19} />} action={<Link className="button button-quiet" to="/connection">Configure backend <ChevronRight size={14} /></Link>} />;
}

function NoResult({ capability, title, detail }: { capability: Capability; title: string; detail: string }) {
  const { states, settings } = useApp();
  if (states[capability] === 'loaded') return null;
  const bound = Boolean(settings.bindings[capability].operationId);
  return <EmptyState title={title} detail={bound ? detail : `${detail} Configure ${capabilityCopy[capability].title.toLowerCase()} in Backend connection.`} icon={<Database size={19} />} action={<Link className="text-link" to="/connection">{bound ? 'Run request' : 'Map backend operation'} <ChevronRight size={14} /></Link>} />;
}

function OverviewPage() {
  const { selectedStudent, studentLabel, selectedRole, results, states, errors, settings, runCapability, mapped } = useApp();
  const [analysisRunning, setAnalysisRunning] = useState(false);
  const navigate = useNavigate();
  const profileName = selectedStudent ? studentLabel(selectedStudent) : '';
  const recommendationItems = mapped('recommendations', 'items');
  const recommendationCount = Array.isArray(recommendationItems) ? recommendationItems.length : undefined;
  const strengths = mapped('skillGap', 'strengths');
  const gaps = mapped('skillGap', 'criticalGaps');
  const ready = selectedStudent && ['placement', 'skillGap', 'recommendations', 'salary'].some((key) => states[key as Capability] === 'loaded');
  const analysisTargets: Capability[] = ['profile', 'placement', 'skillGap', 'recommendations', 'salary'];
  const boundTargets = analysisTargets.filter((key) => settings.bindings[key].operationId);
  const analysisFailures = analysisTargets.filter((key) => Boolean(errors[key]));
  const analyze = async () => {
    if (!selectedStudent || !boundTargets.length || analysisRunning) return;
    setAnalysisRunning(true);
    try { await Promise.allSettled(boundTargets.map((key) => runCapability(key))); }
    finally { setAnalysisRunning(false); }
  };
  const pageFor: Partial<Record<Capability, string>> = { profile: '/profile', placement: '/placement', skillGap: '/skills', recommendations: '/recommendations', salary: '/salary' };
  return <div className="page-stack">
    <PageHeading eyebrow="CAREER INTELLIGENCE / OVERVIEW" title="Student readiness, in context." description="A student-by-student view of what the current profile and connected models report—without replacing their analysis with dashboard assumptions." action={selectedStudent && !boundTargets.length ? <Link className="button button-quiet" to="/connection">Configure backend <ChevronRight size={14} /></Link> : <button className="button button-primary" disabled={!selectedStudent || analysisRunning || !boundTargets.length} onClick={() => void analyze()}>{analysisRunning ? <RefreshCw className="spin" size={15} /> : <RefreshCw size={15} />}{analysisRunning ? 'Analysis running…' : 'Run student analysis'}</button>} />
    {!selectedStudent ? <StudentRequired /> : <>
      <section className="overview-lead surface"><div className="overview-lead-copy"><div className="student-overline"><span className="student-overline-icon"><UserRound size={15} /></span> CURRENTLY SELECTED STUDENT</div><h2>{profileName}</h2><p>Analysis is based on the selected record and connected backend outputs. Change the student in the selector above.</p><div className="overview-meta"><span><GraduationCap size={14} /> Profile selected</span><span><Database size={14} /> {ready ? 'Backend responses loaded' : 'Awaiting analysis'}</span></div></div><div className="overview-lead-visual"><div className="orbit orbit-outer" /><div className="orbit orbit-inner" /><div className="orbit-core"><Activity size={24} /></div><div className="orbit-tag orbit-tag-one">PROFILE</div><div className="orbit-tag orbit-tag-two">MODEL</div><div className="orbit-tag orbit-tag-three">ROLE</div></div></section>
      {analysisRunning && <div className="loading-state overview-running"><RefreshCw className="spin" size={14} />Loading the configured analyses for this student. Each result will appear only after its backend response arrives.</div>}
      {analysisFailures.length > 0 && <section className="surface overview-failures"><SectionTitle title="Some analyses could not be loaded" meta="Retry a failed request or check its binding" />{analysisFailures.map((capability) => <div className="overview-failure-row" key={capability}><span><b>{capabilityCopy[capability].title}</b><small>{errors[capability]}</small></span><div>{pageFor[capability] && <Link className="text-link" to={pageFor[capability]!}>Open page</Link>}<button className="button button-quiet button-small" disabled={states[capability] === 'loading'} onClick={() => void runCapability(capability).catch(() => undefined)}>Retry</button></div></div>)}</section>}
      <div className="three-metrics">
        <MetricCard label="ML placement probability" value={mapped('placement', 'probability')} detail={results.placement ? 'From the placement model response' : 'Not yet returned by the backend'} tone="accent" icon={<Activity size={15} />} />
        <MetricCard label="Placement readiness" value={mapped('placement', 'readiness')} detail="Separate from model probability" icon={<Gauge size={15} />} />
        <MetricCard label="Recommended improvements" value={recommendationCount ?? mapped('recommendations', 'count')} detail="Count from the recommendation response" icon={<Lightbulb size={15} />} />
      </div>
      <div className="two-column-grid overview-secondary">
        <section className="surface overview-list-card"><SectionTitle title="Profile signals" meta="Backend-derived" /><div className="signal-row"><span className="signal-icon signal-positive"><TrendingUp size={16} /></span><div><b>Top strengths</b><p>{present(strengths) ? display(strengths) : 'Not returned by skill-gap analysis.'}</p></div></div><div className="signal-row"><span className="signal-icon signal-warning"><ArrowDownRight size={16} /></span><div><b>Critical skill gaps</b><p>{present(gaps) ? display(gaps) : 'Not returned by skill-gap analysis.'}</p></div></div><div className="signal-row"><span className="signal-icon"><BriefcaseBusinessFallback /></span><div><b>Target role</b><p>{present(mapped('skillGap', 'targetRole')) ? display(mapped('skillGap', 'targetRole')) : selectedRole || 'Not returned. Set a role in Skill Gap Analysis.'}</p></div></div></section>
        <section className="surface overview-salary-card"><SectionTitle title="Salary outlook" meta="Only when available" /><div className="salary-highlight">{present(mapped('salary', 'prediction')) ? display(mapped('salary', 'prediction')) : 'Not available'}</div><p>{present(mapped('salary', 'prediction')) ? 'Backend estimate for this profile; not a guaranteed offer.' : 'No valid salary result has been returned for this student.'}</p><button className="button button-quiet" onClick={() => navigate('/salary')}>View salary analysis <ChevronRight size={14} /></button></section>
      </div>
      <section className="surface overview-actions"><SectionTitle title="Continue the analysis" meta="Student context stays selected across sections" /><div className="action-links"><Link to="/profile"><span className="action-link-icon"><UserRound size={17} /></span><span><b>Review profile</b><small>Fields returned for this student</small></span><ChevronRight size={15} /></Link><Link to="/placement"><span className="action-link-icon"><Target size={17} /></span><span><b>Understand prediction</b><small>Probability and contributing factors</small></span><ChevronRight size={15} /></Link><Link to="/skills"><span className="action-link-icon"><Activity size={17} /></span><span><b>Explore skill gaps</b><small>Current level vs role requirements</small></span><ChevronRight size={15} /></Link><Link to="/recommendations"><span className="action-link-icon"><Sparkles size={17} /></span><span><b>See recommendations</b><small>Prioritized backend actions</small></span><ChevronRight size={15} /></Link></div></section>
      <div className="trust-note"><ShieldAlert size={16} /><span>Placement probability, readiness score and role-based skill gaps are distinct outputs. Predictions are estimates and do not guarantee placement.</span></div>
    </>}
  </div>;
}

function BriefcaseBusinessFallback() { return <GraduationCap size={16} />; }

function ProfilePage() {
  const { selectedStudent, studentLabel, settings, results } = useApp();
  const groups = ['academic', 'technical', 'experience', 'aptitude', 'communication', 'careerTarget'];
  const hasStudent = Boolean(selectedStudent);
  const canCreate = Boolean(settings.bindings.createStudent.operationId);
  if (!hasStudent && !canCreate) return <><PageHeading eyebrow="STUDENT PROFILE" title="Profile, with provenance." description="A structured view of the selected student's real record." /><StudentRequired /></>;
  const mappedGroups = groups.filter((key) => settings.bindings.profile.fieldPaths[key]);
  return <div className="page-stack">
    <PageHeading eyebrow="STUDENT PROFILE" title="Profile, with provenance." description="Academic, technical, experience and career context for the selected student." action={<Link className="button button-quiet" to="/connection">Field mappings <ChevronRight size={14} /></Link>} />
    {!hasStudent && <EmptyState title="No student selected yet" detail="Create a profile from the actual API request schema below, or select a record in the student selector." icon={<GraduationCap size={19} />} />}
    {canCreate && <SchemaForm />}
    {hasStudent && <section className="profile-identity surface"><div className="profile-monogram"><GraduationCap size={24} /></div><div><span className="eyebrow">SELECTED STUDENT</span><h2>{studentLabel(selectedStudent)}</h2><p>Record selected from the connected student source</p></div><div className="profile-completeness"><span>Profile completeness</span><b>{settings.bindings.profile.fieldPaths.completeness && results.profile ? display(getPath(results.profile.value, settings.bindings.profile.fieldPaths.completeness)) : 'Not returned'}</b></div></section>}
    {hasStudent && <CapabilityPanel capability="profile" title="Load complete student profile" description="Returns the profile for the selected record.">
      {results.profile ? <div className="profile-section-grid">{mappedGroups.length ? mappedGroups.map((key) => <article className="surface profile-section" key={key}><div className="profile-section-icon"><BookOpenCheck size={16} /></div><div><h3>{labels[key] || key}</h3><p>{display(getPath(results.profile!.value, settings.bindings.profile.fieldPaths[key]))}</p></div></article>) : <EmptyState title="Profile fields are not mapped" detail="Map academic, technical, experience, aptitude, communication and career-target paths to the backend response. The complete response can still be inspected below." />}</div> : <NoResult capability="profile" title="No profile response loaded" detail="Load the selected student's complete profile from the backend." />}
    </CapabilityPanel>}
    {hasStudent && <section className="surface profile-source"><SectionTitle title="Selected student record" meta="Actual source record · redacted only by your backend" /><pre>{JSON.stringify(selectedStudent, null, 2)}</pre></section>}
    {hasStudent && <div className="profile-actions"><Link className="button button-primary" to="/placement"><Activity size={15} />Continue to placement prediction</Link><span>Run or re-run the profile operation above after changing the selected student.</span></div>}
  </div>;
}

function PlacementPage() {
  const { selectedStudent, mapped, results } = useApp();
  if (!selectedStudent) return <><PageHeading eyebrow="MODEL OUTPUT" title="Placement prediction" description="The connected model's estimate for the selected student—not a promise of outcome." /><StudentRequired /></>;
  const positive = mapped('placement', 'positiveFactors');
  const negative = mapped('placement', 'negativeFactors');
  const list = (value: unknown) => Array.isArray(value) ? value : present(value) ? [value] : [];
  const active = results.placement;
  const factorBox = (title: string, value: unknown, style: 'good' | 'risk') => <section className={`factor-card factor-${style}`}><div className="factor-title"><span>{style === 'good' ? <ArrowUpRight size={15} /> : <ArrowDownRight size={15} />}</span><h3>{title}</h3></div>{list(value).length ? <ul>{list(value).map((item, index) => <li key={index}>{display(item)}</li>)}</ul> : <p className="muted-note">No {title.toLowerCase()} returned by the model explanation.</p>}</section>;
  return <div className="page-stack">
    <PageHeading eyebrow="MODEL OUTPUT / CLASSIFICATION" title="Placement prediction" description="Read the estimate alongside the model context and evidence that shaped it." action={<Link className="button button-quiet" to="/connection">API mappings <ChevronRight size={14} /></Link>} />
    <CapabilityPanel capability="placement" title="Placement model response" description="Current selected-student profile · model outputs only">
      {active ? <><div className="placement-hero"><div className="placement-primary"><div className="eyebrow">PLACEMENT PROBABILITY</div><div className="placement-value">{present(mapped('placement', 'probability')) ? display(mapped('placement', 'probability')) : 'Not returned'}</div><div className="placement-result">{present(mapped('placement', 'prediction')) ? display(mapped('placement', 'prediction')) : 'Prediction result not mapped'}</div><p>Model output is an estimate; it does not guarantee a placement outcome.</p></div><div className="placement-context"><MappedMetrics capability="placement" keys={['risk', 'confidence', 'model', 'generatedAt']} /></div></div><div className="factor-grid">{factorBox('Positive factors', positive, 'good')}{factorBox('Negative factors', negative, 'risk')}</div></> : <NoResult capability="placement" title="Prediction has not been generated" detail="Run the placement prediction for the currently selected student." />}
    </CapabilityPanel>
    {active && <div className="trust-note"><Info size={16} /><span>ML placement probability is not the same as placement readiness or requirement-based skill fit. Only available confidence and explainability fields are shown.</span></div>}
  </div>;
}

interface SkillRow { name: string; current: unknown; required: unknown; gap: unknown; importance: unknown; status: unknown }
function skillRows(raw: unknown, fields: Record<string, string>): SkillRow[] {
  if (!Array.isArray(raw)) return [];
  return raw.map((item, index) => ({
    name: fields.skillName ? display(getPath(item, fields.skillName)) : `Skill ${index + 1}`,
    current: fields.currentLevel ? getPath(item, fields.currentLevel) : undefined,
    required: fields.requiredLevel ? getPath(item, fields.requiredLevel) : undefined,
    gap: fields.gap ? getPath(item, fields.gap) : undefined,
    importance: fields.importance ? getPath(item, fields.importance) : undefined,
    status: fields.status ? getPath(item, fields.status) : undefined,
  }));
}

function SkillTable({ rows, showImportance = true }: { rows: SkillRow[]; showImportance?: boolean }) {
  if (!rows.length) return <EmptyState title="No comparable skills returned" detail="Map the skills collection and its current/required fields from the actual skill-gap response." />;
  return <div className="table-scroll"><table className="data-table"><thead><tr><th>Skill</th><th>Current level</th><th>Required level</th><th>Gap</th>{showImportance && <th>Importance</th>}<th>Status</th></tr></thead><tbody>{rows.map((row, index) => <tr key={`${row.name}-${index}`}><td><strong>{row.name}</strong></td><td>{display(row.current)}</td><td>{display(row.required)}</td><td>{display(row.gap)}</td>{showImportance && <td>{display(row.importance)}</td>}<td>{present(row.status) ? <span className="status-tag">{display(row.status)}</span> : 'Not returned'}</td></tr>)}</tbody></table></div>;
}

function SkillsPage() {
  const { selectedStudent, selectedRole, setSelectedRole, mapped, settings, results, states, errors, runCapability } = useApp();
  const fields = settings.bindings.skillGap.fieldPaths;
  const rows = skillRows(mapped('skillGap', 'skills'), fields);
  const roleData = mapped('roles', 'items');
  const roles = Array.isArray(roleData) ? roleData.map((role) => typeof role === 'string' ? role : settings.bindings.roles.fieldPaths.roleName ? getPath(role, settings.bindings.roles.fieldPaths.roleName) : undefined).filter((item): item is string => typeof item === 'string') : [];
  const numericRows = rows.filter((row) => typeof row.current === 'number' && typeof row.required === 'number').map((row) => ({ skill: row.name, current: row.current as number, required: row.required as number }));
  if (!selectedStudent) return <><PageHeading eyebrow="ROLE REQUIREMENTS / FIT" title="Skill gap analysis" description="Compare this student's returned profile values with the selected role's backend requirements." /><StudentRequired /></>;
  return <div className="page-stack">
    <PageHeading eyebrow="ROLE REQUIREMENTS / FIT" title="Skill gap analysis" description="Current profile values beside actual target-role requirements." action={<Link className="button button-quiet" to="/connection">Map skill fields <ChevronRight size={14} /></Link>} />
    <section className="surface role-toolbar"><div className="role-icon"><Target size={18} /></div><div className="role-toolbar-copy"><b>Target role</b><span>Choose a role from the actual catalog or enter the role used by your backend.</span></div><input list="role-options" value={selectedRole} onChange={(event) => setSelectedRole(event.target.value)} placeholder="Select or enter a backend-supported role" aria-label="Target role" /><datalist id="role-options">{roles.map((role, index) => <option key={`${role}-${index}`} value={role} />)}</datalist><button className="button button-quiet" disabled={states.roles === 'loading'} onClick={() => void runCapability('roles').catch(() => undefined)} title="Load actual role list from backend">{states.roles === 'loading' ? <RefreshCw className="spin" size={14} /> : <ChevronRight size={14} />}{states.roles === 'loading' ? 'Loading roles…' : 'Role catalog'}</button></section>
    {errors.roles && <div className="error-state"><ShieldAlert size={16} /><div><strong>Role catalog could not be loaded</strong><p>{errors.roles}</p><button className="button button-quiet button-small" disabled={states.roles === 'loading'} onClick={() => void runCapability('roles').catch(() => undefined)}>Retry role catalog</button></div></div>}
    <div className="role-controls"><span>Role fit is requirement-based; it is not the ML placement probability.</span><span>{selectedRole ? `Selected role: ${selectedRole}` : 'Select a backend-supported role to request its analysis.'}</span></div>
    <CapabilityPanel capability="skillGap" title="Current vs required" description={selectedRole ? `Selected target: ${selectedRole}` : 'Select a role to request its analysis.'}>
      {results.skillGap ? <><MappedMetrics capability="skillGap" keys={['roleFit']} tone="accent" />{numericRows.length > 0 && <Suspense fallback={<div className="loading-state">Preparing comparison chart…</div>}><SkillComparisonChart rows={numericRows} /></Suspense>}<SkillTable rows={rows} /></> : <NoResult capability="skillGap" title="Skill-gap analysis not loaded" detail="Run the backend skill-gap analysis for the selected target role." />}
    </CapabilityPanel>
    <div className="trust-note"><CircleHelp size={16} /><span>Strong, adequate, needs-improvement and critical-gap labels are displayed only when returned by the role-gap engine.</span></div>
  </div>;
}

function RecommendationsPage() {
  const { selectedStudent, mapped, settings, results } = useApp();
  const raw = mapped('recommendations', 'items');
  const fields = settings.bindings.recommendations.fieldPaths;
  const rows = Array.isArray(raw) ? raw.map((item, index) => ({
    skill: fields.skill ? getPath(item, fields.skill) : undefined,
    priority: fields.priority ? getPath(item, fields.priority) : undefined,
    current: fields.currentLevel ? getPath(item, fields.currentLevel) : undefined,
    required: fields.requiredLevel ? getPath(item, fields.requiredLevel) : undefined,
    gap: fields.gap ? getPath(item, fields.gap) : undefined,
    why: fields.why ? getPath(item, fields.why) : undefined,
    action: fields.action ? getPath(item, fields.action) : undefined,
    impact: fields.expectedImpact ? getPath(item, fields.expectedImpact) : undefined,
    key: index,
  })) : [];
  const priorityOrder = ['high', 'medium', 'low'];
  const groups = priorityOrder.map((priority) => ({ priority, items: rows.filter((row) => String(row.priority || '').toLowerCase().includes(priority)) })).filter((group) => group.items.length);
  const other = rows.filter((row) => !priorityOrder.some((priority) => String(row.priority || '').toLowerCase().includes(priority)));
  if (!selectedStudent) return <><PageHeading eyebrow="PERSONALIZED ACTIONS" title="Recommendations" description="Improvement steps generated for the currently selected student." /><StudentRequired /></>;
  return <div className="page-stack">
    <PageHeading eyebrow="PERSONALIZED ACTIONS" title="Recommendations" description="Prioritized actions from the existing recommendation engine—never generic filler." action={<Link className="button button-quiet" to="/connection">Map recommendation fields <ChevronRight size={14} /></Link>} />
    <CapabilityPanel capability="recommendations" title="Recommendation engine output" description="Actions shown here must be returned for the selected student.">
      {results.recommendations ? rows.length ? <div className="recommendation-groups">{[...groups, ...(other.length ? [{ priority: 'other', items: other }] : [])].map(({ priority, items }) => <section key={priority} className="recommendation-group"><div className="priority-heading"><span className={`priority-dot priority-${priority}`} /><h3>{priority === 'other' ? 'Backend priority' : `${priority[0].toUpperCase()}${priority.slice(1)} priority`}</h3><span>{items.length} returned</span></div>{items.map((item) => <article className="recommendation-card" key={item.key}><div className="recommendation-card-mark"><Lightbulb size={17} /></div><div className="recommendation-content"><div className="recommendation-title-row"><h4>{present(item.skill) ? display(item.skill) : 'Recommendation item'}</h4>{present(item.priority) && <span className="status-tag">{display(item.priority)}</span>}</div><div className="recommendation-metrics"><span>Current <b>{display(item.current)}</b></span><span>Required <b>{display(item.required)}</b></span><span>Gap <b>{display(item.gap)}</b></span></div><p>{present(item.why) ? display(item.why) : 'Reason not returned by the engine.'}</p><div className="recommendation-action"><ArrowUpRight size={14} /><span>{present(item.action) ? display(item.action) : 'Recommended action not returned.'}</span></div>{present(item.impact) && <div className="impact-note"><TrendingUp size={14} />Expected impact: {display(item.impact)}</div>}</div></article>)}</section>)}</div> : <EmptyState title="No recommendations returned" detail="The recommendation response contains no mapped items for this student." /> : <NoResult capability="recommendations" title="No recommendations loaded" detail="Request recommendations from the existing engine." />}
    </CapabilityPanel>
  </div>;
}

function WhatIfPage() {
  const { selectedStudent, mapped, settings, results, runCapability, states, errors } = useApp();
  const [draft, setDraft] = useState<Record<string, string>>({});
  const fields = settings.bindings.skillGap.fieldPaths;
  const rows = skillRows(mapped('skillGap', 'skills'), fields);
  const changed = rows.filter((row) => present(row.current) && (draft[row.name] ?? String(row.current)) !== String(row.current));
  const response = results.whatIf;
  const submit = () => {
    const changes = Object.fromEntries(changed.map((row) => {
      const value = draft[row.name];
      const normalized = typeof row.current === 'number' && value !== undefined && value.trim() !== '' ? Number(value) : value;
      return [row.name, normalized];
    }));
    void runCapability('whatIf', { changes }).catch(() => undefined);
  };
  if (!selectedStudent) return <><PageHeading eyebrow="SCENARIO EXPLORATION" title="What-if analysis" description="Submit revised skill values to the existing model and compare its returned estimates." /><StudentRequired /></>;
  return <div className="page-stack">
    <PageHeading eyebrow="SCENARIO EXPLORATION" title="What if a skill improves?" description="Change values from the selected profile and ask the connected model to recalculate. This page does not predict independently." />
    <div className="whatif-callout"><Activity size={18} /><div><b>Backend recalculation only</b><p>Current levels are sourced from the selected profile/skill-gap response. Changed inputs are sent to the mapped what-if operation.</p></div></div>
    <section className="surface whatif-editor"><SectionTitle title="Edit current skill values" meta={rows.length ? `${rows.length} backend-returned skills` : 'Load skill-gap response first'} />
      {!rows.length ? <><EmptyState title="No actual skill values available" detail="Load the backend skill-gap analysis first. It must return a mapped skills collection and current-level field before values can be edited." action={<button className="button button-quiet" onClick={() => void runCapability('skillGap').catch(() => undefined)} disabled={states.skillGap === 'loading'}><RefreshCw size={14} />{states.skillGap === 'loading' ? 'Loading skill data…' : 'Load skill data'}</button>} />{errors.skillGap && <div className="error-state"><ShieldAlert size={16} /><div><strong>Skill data could not be loaded</strong><p>{errors.skillGap}</p><button className="button button-quiet button-small" disabled={states.skillGap === 'loading'} onClick={() => void runCapability('skillGap').catch(() => undefined)}>Retry skill data</button></div></div>}</> : <div className="whatif-rows">{rows.filter((row) => present(row.current)).map((row) => <label className="whatif-row" key={row.name}><span className="whatif-skill"><b>{row.name}</b><small>Current: {display(row.current)}</small></span><span className="whatif-arrow">→</span><input type={typeof row.current === 'number' ? 'number' : 'text'} step="any" value={draft[row.name] ?? String(row.current)} onChange={(event) => setDraft((previous) => ({ ...previous, [row.name]: event.target.value }))} aria-label={`What-if value for ${row.name}`} /></label>)}<div className="whatif-submit-row"><span>{changed.length ? `${changed.length} value${changed.length === 1 ? '' : 's'} changed` : 'Edit one or more values to run a scenario.'}</span><button className="button button-primary" onClick={submit} disabled={!changed.length || states.whatIf === 'loading'}><Sparkles size={15} />Run what-if analysis</button></div></div>}
    </section>
    <CapabilityPanel capability="whatIf" title="Model scenario response" description="Original and updated values are shown only when returned.">
      {response ? <><MappedMetrics capability="whatIf" keys={['originalProbability', 'updatedProbability', 'difference']} tone="accent" /><MappedData capability="whatIf" keys={['changedSkills', 'effects']} /><div className="whatif-disclaimer">The displayed difference is the backend model result. Skill-level changes do not guarantee real-world placement outcomes.</div></> : <NoResult capability="whatIf" title="No scenario result yet" detail="Submit changed values to the existing backend what-if analysis." />}
    </CapabilityPanel>
  </div>;
}

function SalaryPage() {
  const { selectedStudent, mapped, results } = useApp();
  if (!selectedStudent) return <><PageHeading eyebrow="REGRESSION OUTPUT" title="Salary prediction" description="A backend-provided package estimate, when available for this selected student." /><StudentRequired /></>;
  const prediction = mapped('salary', 'prediction');
  return <div className="page-stack">
    <PageHeading eyebrow="REGRESSION OUTPUT" title="Salary prediction" description="Show only salary values the connected model actually returns." />
    <CapabilityPanel capability="salary" title="Package estimate" description="Valid prediction only · current student profile">
      {results.salary ? present(prediction) ? <><div className="salary-result surface"><div className="salary-result-icon"><WalletIcon /></div><div><span className="eyebrow">BACKEND PREDICTION</span><div className="salary-result-value">{display(prediction)}</div><p>Estimate returned for the selected student; not a guaranteed package.</p></div></div><MappedMetrics capability="salary" keys={['low', 'high', 'currency', 'model']} /><MappedData capability="salary" keys={['factors', 'explanation']} /><div className="trust-note"><ShieldAlert size={16} /><span>Prediction ranges, model context, factors and explanations appear only when supplied by the backend.</span></div></> : <EmptyState title="Salary prediction unavailable" detail="The backend response did not include a valid mapped prediction for this student. No value has been substituted." /> : <NoResult capability="salary" title="Salary prediction not loaded" detail="Request the salary prediction for the selected student." />}
    </CapabilityPanel>
  </div>;
}
function WalletIcon() { return <TrendingUp size={20} />; }

function EdaPage() {
  const { mapped, settings, results } = useApp();
  const keys = ['records', 'features', 'missingValues', 'dataTypes'];
  const chartKeys = ['targetDistribution', 'cgpaDistribution', 'skillDistributions', 'internships', 'projects', 'placements'];
  return <div className="page-stack">
    <PageHeading eyebrow="DATASET INTELLIGENCE" title="Data analysis / EDA" description="Dataset-level distributions and findings—only when returned by the project analysis." />
    <CapabilityPanel capability="eda" title="Dataset overview" description="Counts, distributions and insights from the existing project.">
      {results.eda ? <><MappedMetrics capability="eda" keys={keys} /><Suspense fallback={<div className="loading-state">Preparing dataset charts…</div>}>{chartKeys.filter((key) => settings.bindings.eda.fieldPaths[key] && mapped('eda', key) !== undefined).map((key) => <DistributionChart key={key} title={labels[key] || key} data={mapped('eda', key)} labelPath={settings.bindings.eda.fieldPaths.chartLabel} valuePath={settings.bindings.eda.fieldPaths.chartValue} />)}</Suspense><MappedData capability="eda" keys={['insights', 'correlations']} /></> : <NoResult capability="eda" title="No EDA results loaded" detail="Request actual dataset analysis output from the backend." />}
    </CapabilityPanel>
  </div>;
}

function ModelMetricArtifact({ field, title }: { field: string; title: string }) {
  const { mapped, settings } = useApp();
  const value = mapped('models', field);
  const configured = Boolean(settings.bindings.models.fieldPaths[field]);
  if (!configured && !present(value)) return null;
  const pairs = objectEntries(value);
  const scalarPairs = pairs.length > 0 && pairs.every(([, item]) => item === null || ['string', 'number', 'boolean'].includes(typeof item));
  return <section className="surface model-artifact"><SectionTitle title={title} meta="Backend-supplied metrics" />{!present(value) ? <EmptyState title={`${title} not returned`} detail="The mapped field is absent from this evaluation response." /> : scalarPairs ? <div className="metric-grid">{pairs.map(([name, item]) => <MetricCard key={name} label={name} value={item} />)}</div> : <pre className="model-json">{JSON.stringify(value, null, 2)}</pre>}</section>;
}

function ConfusionMatrixArtifact() {
  const { mapped, settings } = useApp();
  const value = mapped('models', 'confusionMatrix');
  const configured = Boolean(settings.bindings.models.fieldPaths.confusionMatrix);
  if (!configured && !present(value)) return null;
  const numericMatrix = Array.isArray(value) && value.length > 0 && value.every((row) => Array.isArray(row) && row.every((item) => typeof item === 'number')) as boolean;
  if (!numericMatrix) return <MappedData capability="models" keys={['confusionMatrix']} />;
  const matrix = value as number[][];
  const labels = mapped('models', 'classLabels');
  return <section className="surface matrix-card"><SectionTitle title="Confusion matrix" meta="Raw returned counts" /><div className="matrix-caption">Class labels are used only when returned and mapped; otherwise row/column indices are shown.</div><div className="table-scroll"><table className="data-table confusion-matrix"><thead><tr><th>Actual \ Predicted</th>{matrix[0].map((_, index) => <th key={index}>{Array.isArray(labels) && present(labels[index]) ? display(labels[index]) : `Column ${index + 1}`}</th>)}</tr></thead><tbody>{matrix.map((row, rowIndex) => <tr key={rowIndex}><th>{Array.isArray(labels) && present(labels[rowIndex]) ? display(labels[rowIndex]) : `Row ${rowIndex + 1}`}</th>{row.map((item, index) => <td key={index}>{item}</td>)}</tr>)}</tbody></table></div></section>;
}

function MetricValue({ value }: { value: unknown }) {
  const pairs = objectEntries(value);
  const scalarPairs = pairs.length > 0 && pairs.every(([, item]) => item === null || ['string', 'number', 'boolean'].includes(typeof item));
  return scalarPairs ? <div className="model-metric-pairs">{pairs.map(([key, item]) => <span key={key}>{key}<b>{display(item)}</b></span>)}</div> : <span>{display(value)}</span>;
}

function ModelsPage() {
  const { mapped, results, settings } = useApp();
  if (!results.models) return <div className="page-stack"><PageHeading eyebrow="MODEL GOVERNANCE" title="Model performance" description="Classification and regression evaluation artifacts from the actual project run." /><CapabilityPanel capability="models" title="Evaluation results" description="Only generated metrics and model artifacts."><NoResult capability="models" title="Model evaluation data unavailable" detail="Load the project's model evaluation results." /></CapabilityPanel></div>;
  const rawModelRows = mapped('models', 'models');
  const modelRows = Array.isArray(rawModelRows) ? rawModelRows : [];
  const modelFields = settings.bindings.models.fieldPaths;
  const artifactKeys = ['classification', 'regression', 'comparison', 'confusionMatrix', 'roc', 'calibration', 'featureImportance'];
  const hasArtifacts = modelRows.length > 0 || artifactKeys.some((key) => present(mapped('models', key)) || Boolean(modelFields[key]));
  return <div className="page-stack">
    <PageHeading eyebrow="MODEL GOVERNANCE" title="Model performance" description="Classification and regression metrics from the actual model evaluation artifacts." />
    <CapabilityPanel capability="models" title="Evaluation results" description="Metrics are not manually entered in the frontend.">
      {!hasArtifacts && <EmptyState title="No evaluation fields returned or mapped" detail="Map classification/regression metrics or evaluation artifacts from the backend response. No values are manually filled in." />}
      <div className="model-artifact-grid"><ModelMetricArtifact field="classification" title="Classification metrics" /><ModelMetricArtifact field="regression" title="Regression metrics" /></div>
      <ConfusionMatrixArtifact />
      <Suspense fallback={<div className="loading-state">Preparing model charts…</div>}>
        {present(mapped('models', 'roc')) && <RocCurveChart title="ROC curve" data={mapped('models', 'roc')} xPath={modelFields.rocX} yPath={modelFields.rocY} xLabel="False positive rate" yLabel="True positive rate" />}
        {present(mapped('models', 'calibration')) && <RocCurveChart title="Calibration" data={mapped('models', 'calibration')} xPath={modelFields.calibrationX} yPath={modelFields.calibrationY} xLabel="Predicted probability" yLabel="Observed frequency" />}
        {present(mapped('models', 'featureImportance')) && <DistributionChart title="Feature importance" data={mapped('models', 'featureImportance')} labelPath={modelFields.featureName} valuePath={modelFields.featureScore} />}
      </Suspense>
      <MappedData capability="models" keys={['roc', 'calibration', 'featureImportance']} />
      {modelRows.length > 0 && <section className="surface model-comparison"><SectionTitle title="Model comparison" meta="Backend-supplied values" /><div className="table-scroll"><table className="data-table"><thead><tr><th>Model</th><th>Returned performance</th></tr></thead><tbody>{modelRows.map((row, index) => {
        const name = modelFields.modelName ? getPath(row, modelFields.modelName) : undefined;
        const metrics = modelFields.modelMetrics ? getPath(row, modelFields.modelMetrics) : undefined;
        return <tr key={index}><td>{present(name) ? display(name) : 'Model name not mapped'}</td><td>{present(metrics) ? <MetricValue value={metrics} /> : 'Performance fields not mapped'}</td></tr>;
      })}</tbody></table></div></section>}
      {modelRows.length === 0 && <MappedData capability="models" keys={['comparison']} />}
    </CapabilityPanel>
    <div className="trust-note"><Info size={16} /><span>Accuracy, precision, recall, F1, ROC-AUC, MAE, RMSE and R² are rendered only when mapped to fields in the returned evaluation data.</span></div>
  </div>;
}

export default function AnalysisPages({ page }: { page: PageKey }) {
  switch (page) {
    case 'overview': return <OverviewPage />;
    case 'profile': return <ProfilePage />;
    case 'placement': return <PlacementPage />;
    case 'skills': return <SkillsPage />;
    case 'recommendations': return <RecommendationsPage />;
    case 'whatIf': return <WhatIfPage />;
    case 'salary': return <SalaryPage />;
    case 'eda': return <EdaPage />;
    case 'models': return <ModelsPage />;
    default: return null;
  }
}
