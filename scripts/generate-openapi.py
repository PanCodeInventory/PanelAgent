#!/usr/bin/env python3
"""
Generate OpenAPI JSON from the FastAPI application.

This script imports the FastAPI app directly and exports its OpenAPI schema
to a JSON file, which can then be used by openapi-typescript to generate
TypeScript types.

Usage:
    python scripts/generate-openapi.py

Environment:
    PYTHONPATH must be set to the project root for imports to work.
"""

import json
import sys
from pathlib import Path

# Ensure the project root is in the path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def generate_openapi() -> dict:
    """Import the FastAPI app and generate OpenAPI schema."""
    # Import the app - this triggers all the route registration
    from backend.app.main import app
    
    # Get the OpenAPI schema
    openapi_schema = app.openapi()
    return openapi_schema


def main():
    output_path = PROJECT_ROOT / "frontend" / "src" / "lib" / "api" / "openapi.json"
    
    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate the OpenAPI schema
    print(f"Generating OpenAPI schema from FastAPI app...")
    openapi_schema = generate_openapi()
    
    # Write to JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2)
    
    print(f"OpenAPI schema written to: {output_path}")
    
    # Print summary
    paths = openapi_schema.get("paths", {})
    print(f"Exported {len(paths)} paths:")
    for path in sorted(paths.keys()):
        methods = ", ".join(sorted(paths[path].keys()))
        print(f"  {methods.upper()} {path}")


if __name__ == "__main__":
    main()