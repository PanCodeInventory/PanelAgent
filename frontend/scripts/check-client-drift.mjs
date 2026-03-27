/**
 * Check for drift between generated API client and committed files.
 * 
 * This script:
 * 1. Generates the client to a temp location
 * 2. Compares with committed files
 * 3. Exits non-zero if there are differences
 * 
 * Usage: node scripts/check-client-drift.mjs
 */

import { execSync } from 'child_process';
import path from 'path';
import fs from 'fs';
import os from 'os';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const ROOT_DIR = path.resolve(__dirname, '..');
const PROJECT_ROOT = path.resolve(__dirname, '..', '..');
const API_DIR = path.join(ROOT_DIR, 'src', 'lib', 'api');
const GENERATED_DIR = path.join(API_DIR, 'generated');
const TEMP_DIR = fs.mkdtempSync(path.join(os.tmpdir(), 'openapi-drift-'));

function runCommand(cmd, cwd) {
  console.log(`Running: ${cmd}`);
  try {
    execSync(cmd, { 
      cwd, 
      stdio: 'pipe',
      encoding: 'utf-8',
      env: { ...process.env, PYTHONPATH: PROJECT_ROOT }
    });
  } catch (error) {
    return error.stdout || '';
  }
  return '';
}

function cleanup() {
  try {
    fs.rmSync(TEMP_DIR, { recursive: true, force: true });
  } catch {
    // Ignore cleanup errors
  }
}

function main() {
  console.log('=== Checking Client Drift ===\n');
  
  const tempGeneratedDir = path.join(TEMP_DIR, 'generated');
  fs.mkdirSync(tempGeneratedDir, { recursive: true });
  
  console.log('Step 1: Generating OpenAPI JSON...');
  const pythonScript = path.join(PROJECT_ROOT, 'scripts', 'generate-openapi.py');
  runCommand(`python3 ${pythonScript}`, PROJECT_ROOT);
  
  const openapiJson = path.join(API_DIR, 'openapi.json');
  if (!fs.existsSync(openapiJson)) {
    console.error('ERROR: OpenAPI JSON not found');
    cleanup();
    process.exit(1);
  }
  
  console.log('Step 2: Generating types to temp location...');
  const tempOutput = path.join(tempGeneratedDir, 'index.ts');
  runCommand(`npx openapi-typescript "${openapiJson}" --output "${tempOutput}"`, ROOT_DIR);
  
  if (!fs.existsSync(tempOutput)) {
    console.error('ERROR: Failed to generate types to temp location');
    cleanup();
    process.exit(1);
  }
  
  console.log('Step 3: Comparing with committed files...\n');
  
  const committedFile = path.join(GENERATED_DIR, 'index.ts');
  
  if (!fs.existsSync(committedFile)) {
    console.log('No committed generated file exists. This is a fresh generation.');
    console.log('Run "npm run generate:client" to generate and commit the client.');
    cleanup();
    process.exit(1);
  }
  
  const tempContent = fs.readFileSync(tempOutput, 'utf-8');
  const committedContent = fs.readFileSync(committedFile, 'utf-8');
  
  if (tempContent === committedContent) {
    console.log('✓ Client is in sync with backend schema.');
    cleanup();
    process.exit(0);
  } else {
    console.log('✗ DRIFT DETECTED: Client is out of sync with backend schema.');
    console.log('\nThe following changes are needed:');
    console.log('  - Run "npm run generate:client" to update the client');
    console.log('  - Commit the updated files\n');
    
    const tempLines = tempContent.split('\n');
    const committedLines = committedContent.split('\n');
    
    console.log(`Temp file: ${tempLines.length} lines`);
    console.log(`Committed file: ${committedLines.length} lines`);
    
    cleanup();
    process.exit(1);
  }
}

main();