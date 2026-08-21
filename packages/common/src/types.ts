export type MissionStatus =
  | 'DRAFT'
  | 'PARSING_GOAL'
  | 'BUILDING_WORLD_MODEL'
  | 'PLANNING'
  | 'ALLOCATING_RESOURCES'
  | 'READY'
  | 'EXECUTING'
  | 'PAUSED'
  | 'COMPLETED'
  | 'FAILED'
  | 'ABORTED';

export type TaskStatus =
  | 'PENDING'
  | 'READY'
  | 'DISPATCHED'
  | 'RUNNING'
  | 'VERIFYING'
  | 'VERIFIED'
  | 'FAILED'
  | 'SKIPPED'
  | 'PAUSED';

export type AgentRole =
  | 'COORDINATOR'
  | 'ARCHITECT'
  | 'CODER'
  | 'TESTER'
  | 'DEVOPS'
  | 'AUDITOR';

export type VerificationLevel =
  | 'LEVEL_1_SYNTACTIC'
  | 'LEVEL_2_EXECUTION'
  | 'LEVEL_3_ARTIFACT'
  | 'LEVEL_4_SEMANTIC';

export type EpistemicState =
  | 'KNOWN_FACT'
  | 'INFERRED_ASSUMPTION'
  | 'CRITICAL_UNKNOWN';

export interface SuccessCriteriaDTO {
  criteriaId: string;
  description: string;
  verificationLevel: VerificationLevel;
  expectedMetric?: Record<string, unknown> | null;
  isSatisfied: boolean;
  evidenceUri?: string | null;
  evaluationNotes?: string | null;
}

export interface GoalDTO {
  goalStatement: string;
  primaryObjective: string;
  deliverables: string[];
  constraints: Record<string, unknown>;
  successCriteria: SuccessCriteriaDTO[];
}

export interface MissionBudget {
  maxUsdLimit: number;
  maxTotalTokens: number;
  maxExecutionTimeSeconds: number;
  currentUsdSpent: number;
  currentTokensUsed: number;
  currentExecutionTimeSeconds: number;
}

export interface TaskNodeDTO {
  taskId: string;
  missionId: string;
  name: string;
  description: string;
  agentRole: AgentRole;
  status: TaskStatus;
  dependencies: string[];
  dependentChildren: string[];
  inputs: Record<string, unknown>;
  outputs: Record<string, unknown>;
  expectedOutputs: string[];
  idempotencyKey: string;
  retryCount: number;
  maxRetries: number;
  timeoutSeconds: number;
  allocatedTokens: number;
  verificationLevel: VerificationLevel;
  evidenceUri?: string | null;
  errorMessage?: string | null;
  lockedByWorkerId?: string | null;
  createdAt?: string | null;
  startedAt?: string | null;
  completedAt?: string | null;
}

export interface WorldModelEntityDTO {
  entityId: string;
  missionId: string;
  entityType: string;
  name: string;
  properties: Record<string, unknown>;
  epistemicState: EpistemicState;
  confidence: number;
  evidenceUri?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface TelemetryLogEvent {
  timestamp: string;
  missionId: string;
  taskId?: string;
  role: AgentRole;
  level: 'DEBUG' | 'INFO' | 'WARN' | 'ERROR';
  message: string;
  metadata?: Record<string, unknown>;
}
