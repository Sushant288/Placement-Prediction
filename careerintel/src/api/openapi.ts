import type { ApiOperation } from '../types';

const METHODS = new Set(['get', 'post', 'put', 'patch', 'delete', 'options', 'head']);

function resolveSchema(input: unknown, document: Record<string, unknown>, depth = 0): unknown {
  if (depth > 8 || !input || typeof input !== 'object') return input;
  if (Array.isArray(input)) return input.map((item) => resolveSchema(item, document, depth + 1));
  const value = input as Record<string, unknown>;
  const reference = typeof value.$ref === 'string' ? value.$ref : '';
  let resolved: Record<string, unknown> = {};
  if (reference.startsWith('#/')) {
    const target = reference.slice(2).split('/').map((part) => part.replace(/~1/g, '/').replace(/~0/g, '~'))
      .reduce<unknown>((node, part) => node && typeof node === 'object' ? (node as Record<string, unknown>)[part] : undefined, document);
    if (target && typeof target === 'object') resolved = target as Record<string, unknown>;
  }
  const combined = { ...resolved, ...value };
  delete combined.$ref;
  return Object.fromEntries(Object.entries(combined).map(([key, item]) => [key, resolveSchema(item, document, depth + 1)]));
}

export function discoverOperations(document: unknown): ApiOperation[] {
  if (!document || typeof document !== 'object') throw new Error('The API document is not a JSON object.');
  const doc = document as Record<string, unknown>;
  const paths = doc.paths;
  if (!paths || typeof paths !== 'object') throw new Error('No OpenAPI/Swagger paths were found in the document.');
  const output: ApiOperation[] = [];
  for (const [path, rawItem] of Object.entries(paths as Record<string, unknown>)) {
    if (!rawItem || typeof rawItem !== 'object') continue;
    for (const [method, rawOperation] of Object.entries(rawItem as Record<string, unknown>)) {
      if (!METHODS.has(method.toLowerCase()) || !rawOperation || typeof rawOperation !== 'object') continue;
      const op = rawOperation as Record<string, unknown>;
      const operationId = typeof op.operationId === 'string' && op.operationId.trim()
        ? op.operationId
        : `${method.toUpperCase()} ${path}`;
      const requestBody = op.requestBody as { content?: Record<string, { schema?: unknown }> } | undefined;
      const bodyParameter = Array.isArray(op.parameters) ? op.parameters.find((item) => item && typeof item === 'object' && (item as Record<string, unknown>).in === 'body') as Record<string, unknown> | undefined : undefined;
      const rawSchema = requestBody?.content?.['application/json']?.schema ?? bodyParameter?.schema;
      const requestSchema = rawSchema ? resolveSchema(rawSchema, doc) : undefined;
      const summary = typeof op.summary === 'string' ? op.summary : typeof op.description === 'string' ? op.description : '';
      output.push({ operationId, method: method.toUpperCase(), path, summary, requestSchema });
    }
  }
  return output.sort((a, b) => a.path.localeCompare(b.path) || a.method.localeCompare(b.method));
}
