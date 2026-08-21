export const DEFAULT_MISSION_USD_CAP = 5.0;
export const DEFAULT_MISSION_TOKEN_CAP = 1_000_000;
export const DEFAULT_MISSION_TIMEOUT_SECONDS = 3600;
export const DEFAULT_TASK_TIMEOUT_SECONDS = 300;
export const DEFAULT_MAX_RETRIES = 3;

export const PUBSUB_TOPICS = {
  TASK_DISPATCH: 'agentx-task-dispatch',
  TELEMETRY: 'agentx-telemetry-events',
  RECOVERY: 'agentx-recovery-events',
  DEAD_LETTER: 'agentx-dead-letter-queue',
} as const;

export const MODELS = {
  REASONING_PRO: 'gemini-2.5-pro',
  FAST_FLASH: 'gemini-2.5-flash',
  FAST_FLASH_THINKING: 'gemini-2.5-flash-thinking',
  FRONTIER_FLASH: 'gemini-3.7-flash',
  FRONTIER_PRO: 'gemini-3.1-pro',
} as const;
