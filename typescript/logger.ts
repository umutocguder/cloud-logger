/**
 * TypeScript / Node.js Structured Logger with Local Data Custody and Google Cloud Observability.
 */

import * as fs from 'fs';
import * as path from 'path';

export type LogLevel = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';

export interface LogRecord {
  timestamp: string;
  level: LogLevel;
  project_name: string;
  module?: string;
  function?: string;
  message: string;
  execution_time_ms?: number;
  context?: Record<string, any>;
  traceback?: string;
}

export interface LoggerOptions {
  projectName: string;
  logDir?: string;
  logLevel?: LogLevel;
  gcpProjectId?: string;
  enableConsole?: boolean;
}

const LEVEL_SEVERITY: Record<LogLevel, number> = {
  DEBUG: 10,
  INFO: 20,
  WARNING: 30,
  ERROR: 40,
  CRITICAL: 50,
};

export class CloudLoggerTS {
  private projectName: string;
  private logDir: string;
  private minLevel: number;
  private appLogPath: string;
  private errorLogPath: string;
  private enableConsole: boolean;
  private gcpProjectId?: string;

  constructor(options: LoggerOptions) {
    this.projectName = options.projectName;
    this.logDir = options.logDir || path.join(process.cwd(), 'logs');
    this.minLevel = LEVEL_SEVERITY[options.logLevel || 'INFO'] || 20;
    this.enableConsole = options.enableConsole ?? true;
    this.gcpProjectId = options.gcpProjectId || process.env.GCP_PROJECT_ID;

    // Ensure log directory exists
    if (!fs.existsSync(this.logDir)) {
      fs.mkdirSync(this.logDir, { recursive: true });
    }

    this.appLogPath = path.join(this.logDir, 'app.jsonl');
    this.errorLogPath = path.join(this.logDir, 'error.jsonl');
  }

  private shouldLog(level: LogLevel): boolean {
    return (LEVEL_SEVERITY[level] || 20) >= this.minLevel;
  }

  private writeLocal(record: LogRecord): void {
    try {
      const line = JSON.stringify(record) + '\n';
      fs.appendFileSync(this.appLogPath, line, 'utf-8');

      if (record.level === 'ERROR' || record.level === 'CRITICAL') {
        fs.appendFileSync(this.errorLogPath, line, 'utf-8');
      }
    } catch {
      // Zero-crash policy
    }
  }

  private async dispatchGCP(record: LogRecord): Promise<void> {
    if (!this.gcpProjectId) return;
    try {
      // Standard Google Cloud Logging REST API dispatch (non-blocking)
      const token = process.env.GOOGLE_AUTH_TOKEN;
      if (!token) return;

      const url = `https://logging.googleapis.com/v2/entries:write`;
      await fetch(url, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          logName: `projects/${this.gcpProjectId}/logs/${this.projectName}`,
          entries: [
            {
              severity: record.level,
              jsonPayload: record,
              labels: { project_name: this.projectName },
            },
          ],
        }),
      });
    } catch {
      // Zero-crash policy
    }
  }

  private log(
    level: LogLevel,
    message: string,
    context?: Record<string, any>,
    error?: Error | unknown,
    executionTimeMs?: number
  ): void {
    if (!this.shouldLog(level)) return;

    const now = new Date().toISOString();
    let traceback: string | undefined;

    if (error instanceof Error) {
      traceback = error.stack;
    } else if (error) {
      traceback = String(error);
    }

    const record: LogRecord = {
      timestamp: now,
      level,
      project_name: this.projectName,
      message,
      execution_time_ms: executionTimeMs,
      context,
      traceback,
    };

    // 1. Console
    if (this.enableConsole) {
      const timeStr = now.slice(11, 19);
      const prefix = `[${timeStr}] [${level}] [${this.projectName}]`;
      if (level === 'ERROR' || level === 'CRITICAL') {
        console.error(`${prefix} ${message}`, context || '', traceback || '');
      } else {
        console.log(`${prefix} ${message}`, context || '');
      }
    }

    // 2. Local Dual-Write (100% Custody)
    this.writeLocal(record);

    // 3. GCP Dispatch (Fire-and-forget)
    this.dispatchGCP(record).catch(() => {});
  }

  public debug(message: string, context?: Record<string, any>): void {
    this.log('DEBUG', message, context);
  }

  public info(message: string, context?: Record<string, any>): void {
    this.log('INFO', message, context);
  }

  public warn(message: string, context?: Record<string, any>): void {
    this.log('WARNING', message, context);
  }

  public error(message: string, error?: Error | unknown, context?: Record<string, any>): void {
    this.log('ERROR', message, context, error);
  }

  public critical(message: string, error?: Error | unknown, context?: Record<string, any>): void {
    this.log('CRITICAL', message, context, error);
  }
}

export function createLogger(projectName: string, options?: Partial<LoggerOptions>): CloudLoggerTS {
  return new CloudLoggerTS({ projectName, ...options });
}
