/**
 * Settings and configuration for DRMS Node.js implementation.
 */

import { z } from 'zod';
import { config } from 'dotenv';
import { join } from 'path';
import { existsSync, mkdirSync } from 'fs';
import { homedir } from 'os';

// Load environment variables
config();

const SettingsSchema = z.object({
  // Vector Database Settings
  vectorDbPath: z.string().default('./chroma_db_node'),
  useOpenaiEmbeddings: z.boolean().default(false),
  openaiApiKey: z.string().optional(),
  embeddingModel: z.string().default('Xenova/all-MiniLM-L6-v2'),
  
  // Scraping Settings
  cacheDir: z.string().default('./data/cache_node'),
  maxPagesPerLibrary: z.number().default(50),
  scrapingDelay: z.number().default(1.0),
  requestTimeout: z.number().default(30000),
  
  // API Settings
  apiHost: z.string().default('localhost'),
  apiPort: z.number().default(8001),
  enableCors: z.boolean().default(true),
  
  // Logging Settings
  logLevel: z.enum(['DEBUG', 'INFO', 'WARN', 'ERROR']).default('INFO'),
  logFile: z.string().optional(),
  
  // Performance Settings
  maxConcurrentRequests: z.number().default(10),
  chunkSize: z.number().default(500),
  maxResults: z.number().default(20),
  
  // Security Settings
  allowedDomains: z.array(z.string()).default([]),
  blockedDomains: z.array(z.string()).default(['malware.com', 'phishing.com']),
});

export type Settings = z.infer<typeof SettingsSchema>;

class SettingsManager {
  private static instance: SettingsManager;
  private _settings: Settings;

  private constructor() {
    this._settings = this.loadSettings();
    this.createDirectories();
  }

  public static getInstance(): SettingsManager {
    if (!SettingsManager.instance) {
      SettingsManager.instance = new SettingsManager();
    }
    return SettingsManager.instance;
  }

  private loadSettings(): Settings {
    const envSettings = {
      vectorDbPath: process.env.DRMS_VECTOR_DB_PATH,
      useOpenaiEmbeddings: process.env.DRMS_USE_OPENAI_EMBEDDINGS === 'true',
      openaiApiKey: process.env.DRMS_OPENAI_API_KEY || process.env.OPENAI_API_KEY,
      embeddingModel: process.env.DRMS_EMBEDDING_MODEL,
      cacheDir: process.env.DRMS_CACHE_DIR,
      maxPagesPerLibrary: process.env.DRMS_MAX_PAGES_PER_LIBRARY ? parseInt(process.env.DRMS_MAX_PAGES_PER_LIBRARY) : undefined,
      scrapingDelay: process.env.DRMS_SCRAPING_DELAY ? parseFloat(process.env.DRMS_SCRAPING_DELAY) : undefined,
      requestTimeout: process.env.DRMS_REQUEST_TIMEOUT ? parseInt(process.env.DRMS_REQUEST_TIMEOUT) : undefined,
      apiHost: process.env.DRMS_API_HOST,
      apiPort: process.env.DRMS_API_PORT ? parseInt(process.env.DRMS_API_PORT) : undefined,
      enableCors: process.env.DRMS_ENABLE_CORS === 'true',
      logLevel: process.env.DRMS_LOG_LEVEL as 'DEBUG' | 'INFO' | 'WARN' | 'ERROR',
      logFile: process.env.DRMS_LOG_FILE,
      maxConcurrentRequests: process.env.DRMS_MAX_CONCURRENT_REQUESTS ? parseInt(process.env.DRMS_MAX_CONCURRENT_REQUESTS) : undefined,
      chunkSize: process.env.DRMS_CHUNK_SIZE ? parseInt(process.env.DRMS_CHUNK_SIZE) : undefined,
      maxResults: process.env.DRMS_MAX_RESULTS ? parseInt(process.env.DRMS_MAX_RESULTS) : undefined,
      allowedDomains: process.env.DRMS_ALLOWED_DOMAINS ? process.env.DRMS_ALLOWED_DOMAINS.split(',') : undefined,
      blockedDomains: process.env.DRMS_BLOCKED_DOMAINS ? process.env.DRMS_BLOCKED_DOMAINS.split(',') : undefined,
    };

    // Remove undefined values
    const cleanedSettings = Object.fromEntries(
      Object.entries(envSettings).filter(([_, value]) => value !== undefined)
    );

    return SettingsSchema.parse(cleanedSettings);
  }

  private createDirectories(): void {
    const dirs = [this._settings.vectorDbPath, this._settings.cacheDir];
    
    for (const dir of dirs) {
      if (!existsSync(dir)) {
        mkdirSync(dir, { recursive: true });
      }
    }
  }

  public get settings(): Settings {
    return this._settings;
  }

  public isOpenaiConfigured(): boolean {
    return this._settings.useOpenaiEmbeddings && !!this._settings.openaiApiKey;
  }

  public getCachePath(libraryName: string): string {
    return join(this._settings.cacheDir, `${libraryName}_cache.json`);
  }

  public toJSON(): Settings {
    return { ...this._settings };
  }

  public updateSettings(updates: Partial<Settings>): void {
    this._settings = SettingsSchema.parse({ ...this._settings, ...updates });
    this.createDirectories();
  }
}

// Global settings instance
export const getSettings = (): Settings => SettingsManager.getInstance().settings;
export const getSettingsManager = (): SettingsManager => SettingsManager.getInstance();
export { SettingsSchema };