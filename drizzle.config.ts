import { config } from 'dotenv';
import { defineConfig } from 'drizzle-kit';

config(); // Loads .env.local for CLI

export default defineConfig({
  schema: './lib/db/schema.ts',
  out: './lib/db/migrations',
  dialect: 'postgresql',
  dbCredentials: {
    url: process.env.DATABASE_URL!,
  },
});
