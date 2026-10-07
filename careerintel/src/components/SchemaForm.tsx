import { useMemo, useState, type FormEvent } from 'react';
import { AlertCircle, Check, LoaderCircle, UserRoundPlus } from 'lucide-react';
import { useApp } from '../app/AppContext';

interface SchemaProperty { type?: string; title?: string; description?: string; enum?: unknown[]; default?: unknown; format?: string; properties?: Record<string, SchemaProperty>; required?: string[]; items?: unknown }
interface FormField { path: string; name: string; schema: SchemaProperty; group: string; required: boolean }

function humanize(value: string) { return value.split(/[._\-/\s]+/).filter(Boolean).map((part) => part[0].toUpperCase() + part.slice(1)).join(' '); }
function groupFor(value: string) {
  const key = value.toLowerCase();
  if (/cgpa|gpa|backlog|attendance|grade|academic|semester|marks/.test(key)) return 'Academic';
  if (/intern|project|certif|experience|work/.test(key)) return 'Experience';
  if (/skill|program|dsa|sql|web|cloud|python|java|technical|database/.test(key)) return 'Technical skills';
  if (/aptitude|communication|soft|verbal|reason/.test(key)) return 'Aptitude & soft skills';
  if (/role|career|target|job/.test(key)) return 'Career target';
  return 'Additional profile fields';
}
function collectFields(properties: Record<string, SchemaProperty>, parent = '', parentRequired: string[] = [], depth = 0): FormField[] {
  if (depth > 4) return [];
  const fields: FormField[] = [];
  for (const [key, schema] of Object.entries(properties)) {
    if (!schema || typeof schema !== 'object') continue;
    const path = parent ? `${parent}.${key}` : key;
    if (schema.type === 'object' && schema.properties) {
      fields.push(...collectFields(schema.properties, path, schema.required || [], depth + 1));
    } else {
      fields.push({ path, name: schema.title || humanize(key), schema, group: groupFor(`${parent} ${key}`), required: parentRequired.includes(key) });
    }
  }
  return fields;
}
function setPath(target: Record<string, unknown>, path: string, value: unknown) {
  const parts = path.split('.');
  let cursor = target;
  for (const part of parts.slice(0, -1)) {
    if (!cursor[part] || typeof cursor[part] !== 'object') cursor[part] = {};
    cursor = cursor[part] as Record<string, unknown>;
  }
  cursor[parts[parts.length - 1]] = value;
}

export default function SchemaForm() {
  const { settings, operations, runCapability, states, errors } = useApp();
  const binding = settings.bindings.createStudent;
  const operation = operations.find((item) => item.operationId === binding.operationId);
  const schema = operation?.requestSchema as SchemaProperty | undefined;
  const fields = useMemo(() => schema?.properties ? collectFields(schema.properties, '', schema.required || []) : [], [schema]);
  const [values, setValues] = useState<Record<string, string>>({});
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  if (!binding.operationId) return null;

  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError(''); setSuccess(false);
    const missing = fields.find((field) => field.required && !values[field.path]?.trim() && field.schema.default === undefined);
    if (missing) { setError(`${missing.name} is required by the API schema.`); return; }
    const payload: Record<string, unknown> = {};
    try {
      for (const field of fields) {
        const raw = values[field.path];
        if ((raw === undefined || raw === '') && field.schema.default === undefined) continue;
        const input = raw !== undefined && raw !== '' ? raw : field.schema.enum ? JSON.stringify(field.schema.default) : String(field.schema.default ?? '');
        let value: unknown = input;
        if (Array.isArray(field.schema.enum)) {
          const enumIndex = field.schema.enum.findIndex((choice) => JSON.stringify(choice) === input);
          if (enumIndex < 0) throw new Error('Select one of the documented enum values.');
          value = field.schema.enum[enumIndex];
        } else if (field.schema.type === 'number' || field.schema.type === 'integer') value = Number(input);
        else if (field.schema.type === 'boolean') value = input === 'true';
        else if (field.schema.type === 'array' || field.schema.type === 'object') value = JSON.parse(input);
        setPath(payload, field.path, value);
      }
    } catch { setError('One of the array/object fields is not valid JSON.'); return; }
    setSubmitting(true);
    try {
      await runCapability('createStudent', { form: payload });
      setSuccess(true); setValues({});
      if (settings.bindings.students.operationId) await runCapability('students').catch(() => undefined);
    } catch { /* The shared capability error state contains the user-safe request error. */ }
    finally { setSubmitting(false); }
  };

  if (!schema?.properties || !fields.length) return <section className="surface schema-form-card"><div className="section-title"><div><h2>Create a student profile</h2><span>Optional · schema-backed</span></div></div><div className="schema-form-message"><AlertCircle size={17} /><p>The selected operation has no readable JSON request schema. The frontend will not guess profile fields. Provide a schema in the OpenAPI document or use the operation's documented request contract.</p></div></section>;
  const groupOrder = ['Academic', 'Experience', 'Technical skills', 'Aptitude & soft skills', 'Career target', 'Additional profile fields'];
  const groups = groupOrder.map((name) => ({ name, fields: fields.filter((field) => field.group === name) })).filter((group) => group.fields.length);
  const loading = submitting || states.createStudent === 'loading';

  return <section className="surface schema-form-card"><div className="section-title"><div><h2>Create a student profile</h2><span>Fields generated from the connected API request schema</span></div><span className="schema-source">{operation?.method} {operation?.path}</span></div>
    <form onSubmit={submit}>
      {groups.map((group) => <fieldset className="schema-fieldset" key={group.name}><legend>{group.name}</legend><div className="schema-field-grid">{group.fields.map((field) => {
        const fieldType = field.schema.type || 'string';
        const requiredMark = field.required ? <em>Required</em> : null;
        return <label className={`field-label ${fieldType === 'array' || fieldType === 'object' ? 'schema-wide' : ''}`} key={field.path}>{field.name} {requiredMark}<span>{field.schema.description || field.path}</span>
          {Array.isArray(field.schema.enum) ? <select value={values[field.path] ?? ''} required={field.required} onChange={(event) => setValues((previous) => ({ ...previous, [field.path]: event.target.value }))}><option value="">Choose a value…</option>{field.schema.enum.map((choice, index) => <option key={index} value={JSON.stringify(choice)}>{typeof choice === 'object' ? JSON.stringify(choice) : String(choice)}</option>)}</select>
            : fieldType === 'boolean' ? <select value={values[field.path] ?? ''} required={field.required} onChange={(event) => setValues((previous) => ({ ...previous, [field.path]: event.target.value }))}><option value="">Choose true or false…</option><option value="true">True</option><option value="false">False</option></select>
            : fieldType === 'array' || fieldType === 'object' ? <textarea className="code-input" rows={3} value={values[field.path] ?? ''} placeholder={fieldType === 'array' ? '[]' : '{}'} onChange={(event) => setValues((previous) => ({ ...previous, [field.path]: event.target.value }))} />
            : <input type={fieldType === 'integer' || fieldType === 'number' ? 'number' : field.schema.format === 'date' ? 'date' : 'text'} step={fieldType === 'integer' ? '1' : fieldType === 'number' ? 'any' : undefined} required={field.required} value={values[field.path] ?? ''} onChange={(event) => setValues((previous) => ({ ...previous, [field.path]: event.target.value }))} />}
        </label>;
      })}</div></fieldset>)}
      {error && <div className="inline-error"><AlertCircle size={14} />{error}</div>}
      {errors.createStudent && <div className="inline-error"><AlertCircle size={14} />{errors.createStudent}</div>}
      {success && <div className="inline-success"><Check size={14} />Profile submission succeeded. If a student directory is mapped, it has been refreshed; select the returned record in the student selector.</div>}
      <div className="schema-form-submit"><span>Submitted values are sent to the mapped API operation; the frontend does not generate model outputs.</span><button className="button button-primary" disabled={loading} type="submit">{loading ? <LoaderCircle className="spin" size={14} /> : <UserRoundPlus size={14} />}{loading ? 'Submitting…' : 'Create profile'}</button></div>
    </form>
  </section>;
}
