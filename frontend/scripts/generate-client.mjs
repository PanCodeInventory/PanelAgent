/**
 * Generate typed API client from OpenAPI schema.
 * 
 * This script:
 * 1. Runs the Python script to generate OpenAPI JSON
 * 2. Generates TypeScript types using openapi-typescript
 * 
 * Usage: node scripts/generate-client.mjs
 */

import { execSync } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ROOT_DIR = path.resolve(__dirname, '..');
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');
const API_DIR = path.join(ROOT_DIR, 'src', 'lib', 'api');
const OPENAPI_JSON = path.join(API_DIR, 'openapi.json');
const GENERATED_DIR = path.join(API_DIR, 'generated');

function runCommand(cmd, cwd, env = {}) {
  console.log(`Running: ${cmd}`);
  try {
    execSync(cmd, { 
      cwd, 
      stdio: 'inherit',
      env: { ...process.env, PYTHONPATH: PROJECT_ROOT, ...env }
    });
  } catch {
    console.error(`Command failed: ${cmd}`);
    process.exit(1);
  }
}

function main() {
  console.log('=== Generating API Client ===\n');
  
  console.log('Step 1: Generating OpenAPI JSON from FastAPI...');
  const pythonScript = path.join(PROJECT_ROOT, 'scripts', 'generate-openapi.py');
  runCommand(`python3 ${pythonScript}`, PROJECT_ROOT);
  
  if (!fs.existsSync(OPENAPI_JSON)) {
    console.error('ERROR: OpenAPI JSON not found at:', OPENAPI_JSON);
    process.exit(1);
  }
  console.log('OpenAPI JSON generated successfully.\n');
  
  console.log('Step 2: Generating TypeScript types...');
  
  if (!fs.existsSync(GENERATED_DIR)) {
    fs.mkdirSync(GENERATED_DIR, { recursive: true });
  }
  
  runCommand(`npx openapi-typescript "${OPENAPI_JSON}" --output "${GENERATED_DIR}/index.ts"`, ROOT_DIR);
  
  const generatedFile = path.join(GENERATED_DIR, 'index.ts');
  if (!fs.existsSync(generatedFile)) {
    console.error('ERROR: Generated TypeScript file not found at:', generatedFile);
    process.exit(1);
  }
  
  const stats = fs.statSync(generatedFile);
  console.log(`\nGenerated: ${generatedFile} (${stats.size} bytes)`);
  
  console.log('\n=== Client Generation Complete ===');
}

main();