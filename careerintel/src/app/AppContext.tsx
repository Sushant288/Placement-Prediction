import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from 'react';
import { executeOperation, getPath } from '../api/client';
import { discoverOperations } from '../api/openapi';
import { CAPABILITIES, type ApiOperation, type ApiResult, type Bindings, type Capability, type ConnectionSettings, type LoadState, type OperationBinding } from '../types';

const STORE_KEY = 'placement-intelligence-connection-v1';
const emptyBinding = (): OperationBinding => ({ operationId: '', method: '', path: '', requestTemplate: '{}', resultPath: '', fieldPaths: {} });
const emptyBindings = (): Bindings => Object.fromEntries(CAPABILITIES.map((key) => [key, emptyBinding()])) as Bindings;
const defaultSettings: ConnectionSettings = { baseUrl: '', specUrl: '', bindings: emptyBindings() };

function readStoredSettings(): ConnectionSettings {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORE_KEY) || 'null') as Partial<ConnectionSettings> | null;
    if (!parsed) return defaultSettings;
    return { ...defaultSettings, ...parsed, bindings: { ...emptyBindings(), ...(parsed.bindings || {}) } };
  } catch { return defaultSettings; }
}

interface AppContextValue {
  settings: ConnectionSettings;
  setSettings: (value: ConnectionSettings) => void;
  saveSettings: () => void;
  token: string;
  setToken: (value: string) => void;
  operations: ApiOperation[];
  specStatus: 'idle' | 'loading' | 'loaded' | 'error';
  specError: string;
  inspectApi: () => Promise<void>;
  selectedStudent: unknown;
  setSelectedStudent: (value: unknown) => void;
  selectedRole: string;
  setSelectedRole: (value: string) => void;
  results: Partial<Record<Capability, ApiResult>>;
  states: Record<Capability, LoadState>;
  errors: Partial<Record<Capability, string>>;
  runCapability: (capability: Capability, extra?: Record<string, unknown>) => Promise<unknown>;
  mapped: (capability: Capability, field: string) => unknown;
  studentRows: unknown[];
  studentLabel: (student: unknown, index?: number) => string;
}

const Context = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [settings, setSettingsState] = useState<ConnectionSettings>(readStoredSettings);
  const [token, setToken] = useState('');
  const [operations, setOperations] = useState<ApiOperation[]>([]);
  const [specStatus, setSpecStatus] = useState<AppContextValue['specStatus']>('idle');
  const [specError, setSpecError] = useState('');
  const [selectedStudent, setSelectedStudent] = useState<unknown>(null);
  const [selectedRole, setSelectedRole] = useState('');
  const [results, setResults] = useState<Partial<Record<Capability, ApiResult>>>({});
  const [states, setStates] = useState<Record<Capability, LoadState>>(() => Object.fromEntries(CAPABILITIES.map((key) => [key, 'idle'])) as Record<Capability, LoadState>);
  const [errors, setErrors] = useState<Partial<Record<Capability, string>>>({});
  const requestSeq = useRef<Record<Capability, number>>(Object.fromEntries(CAPABILITIES.map((key) => [key, 0])) as Record<Capability, number>);

  const replaceSettings = useCallback((next: ConnectionSettings) => {
    setSettingsState(next);
    for (const capability of CAPABILITIES) requestSeq.current[capability] += 1;
    setResults({});
    setErrors({});
    setStates(Object.fromEntries(CAPABILITIES.map((key) => [key, 'idle'])) as Record<Capability, LoadState>);
  }, []);

  const chooseStudent = useCallback((student: unknown) => {
    const scoped: Capability[] = ['profile', 'placement', 'skillGap', 'recommendations', 'whatIf', 'salary'];
    setSelectedStudent(student);
    setSelectedRole('');
    for (const capability of scoped) requestSeq.current[capability] += 1;
    setResults((previous) => Object.fromEntries(Object.entries(previous).filter(([key]) => !scoped.includes(key as Capability))));
    setErrors((previous) => Object.fromEntries(Object.entries(previous).filter(([key]) => !scoped.includes(key as Capability))));
    setStates((previous) => ({ ...previous, ...Object.fromEntries(scoped.map((key) => [key, 'idle'])) } as Record<Capability, LoadState>));
  }, []);

  const chooseRole = useCallback((role: string) => {
    const scoped: Capability[] = ['placement', 'skillGap', 'recommendations', 'whatIf', 'salary'];
    setSelectedRole(role);
    for (const capability of scoped) requestSeq.current[capability] += 1;
    setResults((previous) => Object.fromEntries(Object.entries(previous).filter(([key]) => !scoped.includes(key as Capability))));
    setErrors((previous) => Object.fromEntries(Object.entries(previous).filter(([key]) => !scoped.includes(key as Capability))));
    setStates((previous) => ({ ...previous, ...Object.fromEntries(scoped.map((key) => [key, 'idle'])) } as Record<Capability, LoadState>));
  }, []);

  const saveSettings = useCallback(() => {
    localStorage.setItem(STORE_KEY, JSON.stringify(settings));
  }, [settings]);

  const inspectApi = useCallback(async () => {
    if (!settings.specUrl.trim()) { setSpecError('Enter the URL of the backend OpenAPI/Swagger document.'); setSpecStatus('error'); return; }
    setSpecStatus('loading'); setSpecError('');
    try {
      const headers: Record<string, string> = { Accept: 'application/json' };
      if (token.trim()) headers.Authorization = `Bearer ${token.trim()}`;
      const response = await fetch(settings.specUrl, { headers });
      if (!response.ok) throw new Error(`The API description returned ${response.status} ${response.statusText}.`);
      const document: unknown = await response.json();
      const found = discoverOperations(document);
      if (!found.length) throw new Error('No supported operations were found in the API description.');
      setOperations(found); setSpecStatus('loaded');
    } catch (error) {
      setOperations([]); setSpecStatus('error');
      setSpecError(error instanceof Error ? error.message : 'The API description could not be loaded. Check its URL and CORS settings.');
    }
  }, [settings.specUrl, token]);

  const runCapability = useCallback(async (capability: Capability, extra: Record<string, unknown> = {}) => {
    const binding = settings.bindings[capability];
    const requestId = ++requestSeq.current[capability];
    setStates((previous) => ({ ...previous, [capability]: 'loading' }));
    setErrors((previous) => ({ ...previous, [capability]: undefined }));
    try {
      const value = await executeOperation({
        baseUrl: settings.baseUrl,
        token,
        binding,
        context: { student: selectedStudent, role: selectedRole, ...extra },
      });
      if (requestSeq.current[capability] !== requestId) return value;
      setResults((previous) => ({ ...previous, [capability]: { value, receivedAt: new Date().toISOString(), operationId: binding.operationId } }));
      setStates((previous) => ({ ...previous, [capability]: 'loaded' }));
      return value;
    } catch (error) {
      if (requestSeq.current[capability] !== requestId) throw error;
      const message = error instanceof Error ? error.message : 'The backend request could not be completed.';
      setErrors((previous) => ({ ...previous, [capability]: message }));
      setStates((previous) => ({ ...previous, [capability]: 'error' }));
      throw error;
    }
  }, [settings, token, selectedStudent, selectedRole]);

  const mapped = useCallback((capability: Capability, field: string) => {
    const result = results[capability];
    const path = settings.bindings[capability].fieldPaths[field];
    return result && path ? getPath(result.value, path) : undefined;
  }, [results, settings.bindings]);

  const studentRows = useMemo(() => {
    const value = results.students?.value;
    if (Array.isArray(value)) return value;
    return [];
  }, [results.students]);

  const studentLabel = useCallback((student: unknown, index = 0) => {
    const fields = settings.bindings.students.fieldPaths;
    const name = fields.name ? getPath(student, fields.name) : undefined;
    const id = fields.id ? getPath(student, fields.id) : undefined;
    if (name !== undefined && name !== null && String(name).trim()) return String(name);
    if (id !== undefined && id !== null && String(id).trim()) return `Student ${String(id)}`;
    return `Record ${index + 1} · map a name or ID field`;
  }, [settings.bindings.students.fieldPaths]);

  const value: AppContextValue = {
    settings, setSettings: replaceSettings, saveSettings, token, setToken, operations, specStatus, specError, inspectApi,
    selectedStudent, setSelectedStudent: chooseStudent, selectedRole, setSelectedRole: chooseRole, results, states, errors,
    runCapability, mapped, studentRows, studentLabel,
  };
  return <Context.Provider value={value}>{children}</Context.Provider>;
}

export function useApp() {
  const value = useContext(Context);
  if (!value) throw new Error('useApp must be used inside AppProvider.');
  return value;
}
