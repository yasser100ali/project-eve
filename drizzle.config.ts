import { config } from 'dotenv';
import { defineConfig } from 'drizzle-kit';
import { neon } from '@neondatabase/serverless';

config(); // Loads .env.local for CLI

export default defineConfig({
  schema: './lib/db/schema.ts',
  out: './lib/db/migrations',
  dialect: 'postgresql',
  dbCredentials: neon(process.env.DATABASE_URL!),
});
