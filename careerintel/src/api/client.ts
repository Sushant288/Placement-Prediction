import type { OperationBinding } from '../types';

export function getPath(source: unknown, path: string): unknown {
  if (!path.trim() || path.trim() === '$') return source;
  const tokens = [...path.replace(/^\$\.?/, '').matchAll(/([^.[\]]+)|\[(\d+)\]|\[['"]([^'"]+)['"]\]/g)]
    .map((m) => m[1] ?? m[2] ?? m[3]);
  return tokens.reduce<unknown>((current, key) => {
    if (current === null || current === undefined) return undefined;
    return (current as Record<string, unknown>)[key];
  }, source);
}

function readContext(context: Record<string, unknown>, key: string): unknown {
  return getPath(context, key);
}

function expand(value: unknown, context: Record<string, unknown>): unknown {
  if (typeof value === 'string') {
    const wholeValue = value.match(/^\{\{\s*([^{}]+?)\s*\}\}$/);
    if (wholeValue) {
      const result = readContext(context, wholeValue[1].trim());
      if (result === undefined || result === null) throw new Error(`Missing request value: ${wholeValue[1].trim()}`);
      return result;
    }
    return value.replace(/\{\{\s*([^{}]+?)\s*\}\}/g, (_match, key: string) => {
      const result = readContext(context, key.trim());
      if (result === undefined || result === null) throw new Error(`Missing request value: ${key.trim()}`);
      return typeof result === 'object' ? JSON.stringify(result) : String(result);
    });
  }
  if (Array.isArray(value)) return value.map((item) => expand(item, context));
  if (value && typeof value === 'object') {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, expand(item, context)]));
  }
  return value;
}

export async function executeOperation(args: {
  baseUrl: string;
  token: string;
  binding: OperationBinding;
  context: Record<string, unknown>;
  signal?: AbortSignal;
}): Promise<unknown> {
  const { baseUrl, token, binding, context, signal } = args;
  if (!binding.operationId || !binding.path || !binding.method) throw new Error('This capability has no API operation mapped yet. Configure it in Backend connection.');
  let bodyConfig: unknown;
  try { bodyConfig = expand(JSON.parse(binding.requestTemplate || '{}'), context); }
  catch (error) { throw new Error(error instanceof Error ? error.message : 'Check the request-template JSON.'); }
  const route = expand(binding.path, context) as string;
  const root = baseUrl.replace(/\/+$/, '');
  if (!root) throw new Error('Enter the backend base URL in Backend connection.');
  const url = new URL(`${root}${route.startsWith('/') ? route : `/${route}`}`);
  const method = binding.method.toUpperCase();
  const headers: Record<string, string> = { Accept: 'application/json' };
  if (token.trim()) headers.Authorization = `Bearer ${token.trim()}`;
  const init: RequestInit = { method, headers, signal };
  if (['GET', 'DELETE', 'HEAD'].includes(method)) {
    if (bodyConfig && typeof bodyConfig === 'object' && !Array.isArray(bodyConfig)) {
      for (const [key, value] of Object.entries(bodyConfig as Record<string, unknown>)) {
        if (value !== undefined && value !== null) url.searchParams.set(key, typeof value === 'string' ? value : JSON.stringify(value));
      }
    }
  } else {
    headers['Content-Type'] = 'application/json';
    init.body = JSON.stringify(bodyConfig);
  }
  let response: Response;
  try { response = await fetch(url, init); }
  catch { throw new Error('Could not reach the backend. Check the URL, network access, and backend CORS settings.'); }
  const text = await response.text();
  let payload: unknown = null;
  if (text) {
    try { payload = JSON.parse(text); }
    catch { payload = text; }
  }
  if (!response.ok) {
    throw new Error(`Backend request failed with HTTP ${response.status}. Check the selected operation, request mapping, and authorization.`);
  }
  return binding.resultPath ? getPath(payload, binding.resultPath) : payload;
}

export function mappedFields(value: unknown, fields: Record<string, string>): Record<string, unknown> {
  return Object.fromEntries(Object.entries(fields).map(([key, path]) => [key, path ? getPath(value, path) : undefined]));
}
