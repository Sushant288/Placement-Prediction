export const CAPABILITIES = [
  'students', 'createStudent', 'profile', 'placement', 'roles', 'skillGap', 'recommendations',
  'whatIf', 'salary', 'eda', 'models',
] as const;

export type Capability = (typeof CAPABILITIES)[number];

export const CAPABILITY_LABELS: Record<Capability, string> = {
  students: 'Student directory',
  createStudent: 'Create student profile',
  profile: 'Student profile',
  placement: 'Placement prediction',
  roles: 'Target roles',
  skillGap: 'Skill-gap analysis',
  recommendations: 'Recommendations',
  whatIf: 'What-if analysis',
  salary: 'Salary prediction',
  eda: 'Dataset analysis / EDA',
  models: 'Model performance',
};

export interface ApiOperation {
  operationId: string;
  method: string;
  path: string;
  summary: string;
  requestSchema?: unknown;
}

export interface OperationBinding {
  operationId: string;
  method: string;
  path: string;
  requestTemplate: string;
  resultPath: string;
  fieldPaths: Record<string, string>;
}

export type Bindings = Record<Capability, OperationBinding>;

export interface ConnectionSettings {
  baseUrl: string;
  specUrl: string;
  bindings: Bindings;
}

export interface ApiResult {
  value: unknown;
  receivedAt: string;
  operationId: string;
}

export type LoadState = 'idle' | 'loading' | 'loaded' | 'error';
