import { useMemo, useState } from 'react';
import { ArrowRight, Check, CircleHelp, Cloud, Link2, LockKeyhole, RefreshCw, Save, Search, ShieldCheck, Unplug } from 'lucide-react';
import { useApp } from '../app/AppContext';
import { PageHeading, SectionTitle } from '../components/shared';
import { CAPABILITIES, CAPABILITY_LABELS, type Capability } from '../types';

const FIELD_HINTS: Record<Capability, string[]> = {
  students: ['id', 'name'],
  createStudent: [],
  profile: ['academic', 'technical', 'experience', 'aptitude', 'communication', 'careerTarget', 'completeness'],
  placement: ['probability', 'prediction', 'readiness', 'risk', 'confidence', 'model', 'generatedAt', 'positiveFactors', 'negativeFactors'],
  roles: ['items', 'roleName'],
  skillGap: ['roleFit', 'targetRole', 'skills', 'strengths', 'criticalGaps', 'skillName', 'currentLevel', 'requiredLevel', 'gap', 'importance', 'status'],
  recommendations: ['items', 'skill', 'currentLevel', 'requiredLevel', 'gap', 'priority', 'why', 'action', 'expectedImpact'],
  whatIf: ['originalProbability', 'updatedProbability', 'difference', 'changedSkills', 'effects'],
  salary: ['prediction', 'low', 'high', 'currency', 'model', 'factors', 'explanation'],
  eda: ['records', 'features', 'targetDistribution', 'missingValues', 'dataTypes', 'cgpaDistribution', 'skillDistributions', 'internships', 'projects', 'placements', 'correlations', 'insights', 'chartLabel', 'chartValue'],
  models: ['classification', 'regression', 'comparison', 'models', 'modelName', 'modelMetrics', 'confusionMatrix', 'classLabels', 'roc', 'rocX', 'rocY', 'calibration', 'calibrationX', 'calibrationY', 'featureImportance', 'featureName', 'featureScore'],
};

export default function ConnectionPage() {
  const { settings, setSettings, saveSettings, token, setToken, operations, specStatus, specError, inspectApi } = useApp();
  const [saved, setSaved] = useState(false);
  const [fieldDrafts, setFieldDrafts] = useState<Record<string, string>>({});
  const [jsonErrors, setJsonErrors] = useState<Record<string, string>>({});
  const selectedBindings = useMemo(() => CAPABILITIES.filter((key) => settings.bindings[key].operationId).length, [settings.bindings]);

  const updateBinding = (capability: Capability, patch: Partial<(typeof settings.bindings)[Capability]>) => {
    setSettings({ ...settings, bindings: { ...settings.bindings, [capability]: { ...settings.bindings[capability], ...patch } } });
    setSaved(false);
  };

  const save = () => {
    saveSettings();
    setSaved(true);
  };

  return <div className="page-stack connection-page">
    <PageHeading eyebrow="INTEGRATION SETUP" title="Connect your analysis backend" description="Discover the API contract first. Bind real operations and response fields; no endpoint names or result formats are assumed." />

    <section className="surface connection-intro"><div className="intro-icon"><Link2 size={20} /></div><div><strong>Frontend only · no model logic duplicated</strong><p>The browser calls the API you configure. Model outputs, student records and metrics are rendered only when the service returns them.</p></div><div className="intro-status"><span className={`status-dot ${operations.length ? 'online' : ''}`} />{operations.length ? `${operations.length} operations discovered` : 'Not connected'}</div></section>

    <section className="surface connection-card"><SectionTitle title="1 · API location" meta="OpenAPI or Swagger JSON · Browser access must allow CORS" />
      <div className="connection-fields"><label className="field-label">Backend base URL<span>Origin or API root</span><input type="url" value={settings.baseUrl} onChange={(event) => { setSettings({ ...settings, baseUrl: event.target.value }); setSaved(false); }} placeholder="https://your-api.example.com" /></label>
        <label className="field-label">API description URL<span>OpenAPI / Swagger JSON document</span><input type="url" value={settings.specUrl} onChange={(event) => { setSettings({ ...settings, specUrl: event.target.value }); setSaved(false); }} placeholder="https://your-api.example.com/openapi.json" /></label>
        <label className="field-label field-full">Optional bearer token<span><LockKeyhole size={12} /> Kept in memory for this page session; never saved to local storage.</span><input type="password" autoComplete="off" value={token} onChange={(event) => setToken(event.target.value)} placeholder="Paste a short-lived API token if required" /></label>
      </div>
      <div className="connection-actions"><button className="button button-primary" onClick={() => void inspectApi()} disabled={specStatus === 'loading'}><Search size={15} />{specStatus === 'loading' ? 'Inspecting API…' : 'Inspect API document'}</button><span className="helper-inline">This loads the API description only; it does not run student analysis.</span></div>
      {specStatus === 'loaded' && <div className="inline-success"><Check size={15} />Discovered {operations.length} operations. Bind the relevant operations below.</div>}
      {specError && <div className="inline-error"><Unplug size={15} />{specError}</div>}
    </section>

    <section className="surface connection-card"><SectionTitle title="2 · Capability bindings" meta={`${selectedBindings} of ${CAPABILITIES.length} mapped`} />
      <p className="section-explainer">Choose an operation discovered from your own API. Enter a result path only when the response wraps the value (for example, an array nested in an object); leave blank to retain the full response. Request JSON is sent as query parameters for GET/DELETE and as a JSON body for other methods. Template values may reference <code>{'{{student.<field>}}'}</code>, <code>{'{{role}}'}</code>, <code>{'{{changes}}'}</code>, or the schema-backed profile form's <code>{'{{form}}'}</code>. For EDA charts, map <code>chartLabel</code>/<code>chartValue</code> for array responses; otherwise the chart renderer accepts a numeric category-to-value object. Other shapes remain visible in the raw response.</p>
      {CAPABILITIES.map((capability) => {
        const binding = settings.bindings[capability];
        const draftKey = `${capability}-fields`;
        const fieldText = fieldDrafts[draftKey] ?? JSON.stringify(binding.fieldPaths, null, 2);
        return <details className="binding-row" key={capability} open={capability === 'students' && !binding.operationId}>
          <summary><span className="binding-icon"><Cloud size={16} /></span><span className="binding-title"><b>{CAPABILITY_LABELS[capability]}</b><small>{binding.operationId ? `${binding.method} ${binding.path}` : 'Not mapped · analysis will remain unavailable'}</small></span><span className={`binding-pill ${binding.operationId ? 'binding-configured' : ''}`}>{binding.operationId ? 'Mapped' : 'Unmapped'}</span><ArrowRight size={14} className="binding-chevron" /></summary>
          <div className="binding-content">
            <label className="field-label">Discovered operation<select value={binding.operationId} onChange={(event) => {
              const operation = operations.find((item) => item.operationId === event.target.value);
              updateBinding(capability, operation ? { operationId: operation.operationId, method: operation.method, path: operation.path, requestTemplate: capability === 'createStudent' && binding.requestTemplate.trim() === '{}' ? '"{{form}}"' : binding.requestTemplate } : { operationId: '', method: '', path: '' });
            }}><option value="">Choose from the loaded API contract…</option>{operations.map((operation) => <option key={`${operation.method}:${operation.path}`} value={operation.operationId}>{operation.method} · {operation.path} — {operation.operationId}</option>)}</select></label>
            {binding.operationId && <div className="selected-operation-summary"><span>{binding.method}</span><code>{binding.path}</code>{operations.find((item) => item.operationId === binding.operationId)?.summary && <small>{operations.find((item) => item.operationId === binding.operationId)?.summary}</small>}</div>}
            <label className="field-label">Request template JSON<span>Use actual request field names from the API schema; blank substitutions are rejected before sending.</span><textarea className="code-input" rows={3} value={binding.requestTemplate} onChange={(event) => updateBinding(capability, { requestTemplate: event.target.value })} spellCheck={false} /></label>
            <label className="field-label">Response result path<span>Optional path to the object/list used by the page (dot paths, array indexes and <code>$</code> prefix supported).</span><input value={binding.resultPath} onChange={(event) => updateBinding(capability, { resultPath: event.target.value })} placeholder="Leave blank to keep the complete response" /></label>
            <label className="field-label">Semantic field mappings<span>JSON from UI field name to a path in the response. Only mapped fields appear as named metrics; unknown values stay in the raw response viewer.</span><textarea className="code-input" rows={Math.max(5, FIELD_HINTS[capability].length + 1)} value={fieldText} spellCheck={false} onChange={(event) => {
              setFieldDrafts((draft) => ({ ...draft, [draftKey]: event.target.value }));
              try { const fields = JSON.parse(event.target.value) as Record<string, string>; if (fields && typeof fields === 'object' && !Array.isArray(fields)) { updateBinding(capability, { fieldPaths: fields }); setJsonErrors((current) => ({ ...current, [draftKey]: '' })); } else throw new Error('Use a JSON object.'); }
              catch { setJsonErrors((current) => ({ ...current, [draftKey]: 'Keep the mappings as a JSON object of UI field names to response paths.' })); }
            }} /></label>
            {jsonErrors[draftKey] && <div className="inline-error small-error">{jsonErrors[draftKey]}</div>}
            <div className="suggested-fields"><span>Useful UI keys:</span>{FIELD_HINTS[capability].map((key) => <code key={key}>{key}</code>)}</div>
          </div>
        </details>;
      })}
      <div className="connection-actions connection-save"><button className="button button-primary" onClick={save}><Save size={15} />Save connection &amp; mappings</button>{saved && <span className="inline-success no-margin"><ShieldCheck size={15} />Saved in this browser (token excluded).</span>}<button className="button button-quiet" onClick={() => void inspectApi()} disabled={!settings.specUrl || specStatus === 'loading'}><RefreshCw size={14} />Refresh operation list</button></div>
    </section>

    <section className="connection-help"><CircleHelp size={17} /><div><strong>No backend contract was supplied with this project.</strong><p>The app is intentionally unconfigured: student records, predictions, role requirements, recommendations, salary results, EDA and model metrics will not be fabricated. To finish verified integration, supply the backend repository/source or its API base URL and OpenAPI/endpoint documentation. To call an API from this browser, its CORS policy must allow this site.</p></div></section>
  </div>;
}
