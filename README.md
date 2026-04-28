# PanelAgent

[![Next.js](https://img.shields.io/badge/Next.js-16.2.1-black?logo=next.js)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19.2.4-61DAFB?logo=react)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python)](https://python.org/)
[![Deepseek](https://img.shields.io/badge/Deepseek-v4--pro-412991?logo=openai)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**AI-powered multi-color flow cytometry panel design tool for immunologists and flow cytometry researchers.**

PanelAgent combines deterministic algorithms with Large Language Model (LLM) evaluation to generate physically valid flow cytometry panels grounded in real antibody inventory data. It helps researchers design optimal antibody panels by considering spectral overlap, fluorochrome brightness, and experimental requirements.

## Table of Contents

- [Background](#background)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the Application](#running-the-application)
- [Admin Interface](#admin-interface)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Development](#development)
- [Docker Deployment](#docker-deployment)
- [Contributing](#contributing)
- [License](#license)

## Background

Flow cytometry panel design is a complex task requiring expertise in immunology, fluorescence spectroscopy, and instrument configuration. Researchers must balance multiple constraints:

- Spectral overlap between fluorochromes
- Antibody availability and quality
- Marker expression patterns on target cells
- Instrument detector configurations

PanelAgent addresses these challenges by providing an intelligent assistant that:

1. **Understands experimental goals** through natural language descriptions
2. **Generates physically valid panels** based on available antibody inventory
3. **Evaluates panel quality** considering spectral characteristics
4. **Tracks antibody quality issues** through a quality registry system

## Features

### AI Experimental Design

Describe your experimental goals in natural language and receive AI-recommended marker combinations tailored to your research needs.

### Panel Generation

Generate multi-color flow cytometry panels automatically based on:
- Available antibody inventory (human/mouse)
- Target markers and fluorochromes
- Spectral compatibility constraints
- Instrument channel configurations

### Panel Evaluation & Diagnosis

Evaluate existing panels for:
- Spectral overlap issues
- Fluorochrome brightness compatibility
- Spillover spreading calculations
- Viability and data quality predictions

### Quality Registry

Track and manage antibody quality issues:
- Record lot-specific quality problems
- Project quality scores for specific markers
- View quality history and trends
- Export quality data for analysis

### Marker Recommendations

Get intelligent marker suggestions based on:
- Cell type identification requirements
- Functional marker requirements
- Lineage marker combinations
- Literature-based recommendations

### Spectral Analysis

Visualize fluorochrome spectral characteristics:
- Excitation/emission spectra
- Detector channel mappings
- Relative brightness comparisons

## Tech Stack

| Layer | Technology |
|-------|------------|
| **User Frontend** | Next.js 16.2.1, React 19.2.4, TypeScript |
| **Admin Frontend** | Next.js 16.2.1, React 19.2.4, TypeScript |
| **UI Framework** | shadcn/ui (Base UI + Tailwind CSS 4) |
| **Charts** | Recharts 3.8.1 |
| **AI Integration** | Vercel AI SDK, OpenAI API |
| **Backend** | FastAPI 0.115+, Python 3.13+ |
| **Data Processing** | Pandas, NumPy, SciPy |
| **Reverse Proxy** | Nginx (gateway) |
| **Testing** | Playwright (E2E), Pytest |

## Architecture

PanelAgent uses a **dual-frontend architecture** with a shared backend:

```
                        ┌──────────────────┐
                        │  Gateway (nginx) │
                        │  localhost:8080   │
                        └────────┬─────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 │               │               │
          /admin/*        /api/v1/*          /*
                 │               │               │
        ┌────────▼──────┐       │      ┌────────▼──────┐
        │ Admin Frontend │       │      │ User Frontend │
        │ localhost:3001 │       │      │ localhost:3000 │
        └────────┬──────┘       │      └────────┬──────┘
                 │              │               │
                 └──────────────┼───────────────┘
                                │
                       ┌────────▼─────────┐
                       │     Backend      │
                       │  localhost:8000  │
                       └──────────────────┘
```

### Service Ports

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| Backend | 8000 | `http://localhost:8000` | FastAPI REST API |
| User Frontend | 3000 | `http://localhost:3000` | User-facing Next.js app |
| Admin Frontend | 3001 | `http://localhost:3001` | Admin Next.js app |
| Gateway | 8080 | `http://localhost:8080` | Nginx reverse proxy (all services) |

### Request Routing

The nginx gateway routes requests based on URL prefix:

| Browser Path | Routes To | Backend API Path |
|--------------|-----------|------------------|
| `/` | User Frontend (3000) | — |
| `/exp-design` | User Frontend (3000) | — |
| `/panel-design` | User Frontend (3000) | — |
| `/quality-registry` | User Frontend (3000) | — |
| `/api/v1/*` | User Frontend (3000) → Backend (8000) | `/api/v1/*` |
| `/admin/login` | Admin Frontend (3001) | — |
| `/admin/settings` | Admin Frontend (3001) | — |
| `/admin/history` | Admin Frontend (3001) | — |
| `/admin/api/v1/*` | Admin Frontend (3001) → Backend (8000) | `/api/v1/admin/*` |

## Getting Started

### Prerequisites

- **Node.js** 18+ and npm/pnpm
- **Python** 3.13+
- **OpenAI API access** (or compatible API endpoint)
- **Docker** (optional, for containerized deployment)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/PanelAgent.git
cd PanelAgent
```

2. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

3. Install user frontend dependencies:
```bash
cd frontend
npm install
```

4. Install admin frontend dependencies:
```bash
cd admin-frontend
npm install
```

### Configuration

Create environment files with your configuration:

**Backend (`backend/.env` or root `.env`):**
```bash
# OpenAI API Configuration
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL_NAME=gpt-4o

# Admin Authentication
ADMIN_PASSWORD=your-secure-admin-password
ADMIN_SESSION_SECRET=your-session-secret  # auto-generated if omitted
```

**User Frontend (`frontend/.env.local`):**
```bash
# Backend API URL (internal)
BACKEND_INTERNAL_URL=http://127.0.0.1:8000

# Public backend URL (if different)
BACKEND_PUBLIC_URL=http://localhost:8000
```

**Admin Frontend (`admin-frontend/.env.local`):**
```bash
# Backend API URL (internal)
BACKEND_INTERNAL_URL=http://127.0.0.1:8000
```

#### Environment Variables Reference

| Variable | Service | Required | Description |
|----------|---------|----------|-------------|
| `OPENAI_API_KEY` | Backend | Yes | OpenAI API key for LLM features |
| `OPENAI_API_BASE` | Backend | No | Custom API endpoint (default: OpenAI) |
| `OPENAI_MODEL_NAME` | Backend | No | Model to use (default: `gpt-4o`) |
| `ADMIN_PASSWORD` | Backend | Yes | Password for admin login |
| `ADMIN_SESSION_SECRET` | Backend | No | Session encryption key (auto-generated if missing) |
| `BACKEND_INTERNAL_URL` | Frontend/Admin | Yes | Backend URL for server-side API calls |
| `BACKEND_PUBLIC_URL` | Frontend | No | Public-facing backend URL |

### Running the Application

#### Option 1: Make Commands (Recommended)

Start all services at once:
```bash
make dev-all
```

Or start individual services:
```bash
make dev-backend         # Backend on port 8000
make dev-frontend        # User frontend on port 3000
make dev-admin-frontend  # Admin frontend on port 3001
```

#### Option 2: Manual Startup

**Terminal 1 — Backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — User Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 — Admin Frontend:**
```bash
cd admin-frontend
npm run dev -- --port 3001
```

#### Option 3: Docker Compose

```bash
docker compose build
docker compose up -d
```

This starts all services including the nginx gateway on port 8080.

#### Accessing the Application

| Interface | URL |
|-----------|-----|
| User App (direct) | `http://localhost:3000` |
| Admin App (direct) | `http://localhost:3001/login` |
| All services (gateway) | `http://localhost:8080` |
| Admin (via gateway) | `http://localhost:8080/admin/login` |
| API (via gateway) | `http://localhost:8080/api/v1/` |

## Admin Interface

The admin interface provides system management capabilities separate from the user-facing application.

### Access

- **Via gateway**: `http://localhost:8080/admin/login`
- **Direct**: `http://localhost:3001/login`

### Authentication

Log in using the password configured via the `ADMIN_PASSWORD` environment variable. The session is managed server-side with cookies.

### Admin Features

| Page | Path | Description |
|------|------|-------------|
| Login | `/admin/login` | Admin authentication |
| Settings | `/admin/settings` | LLM model configuration, API keys |
| History | `/admin/history` | Panel generation history and audit |
| Quality Registry | `/admin/quality-registry` | Review, resolve, and manage quality issues |

### Admin API

All admin API endpoints are prefixed with `/api/v1/admin/` and require authentication:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/admin/auth/login` | POST | Admin login |
| `/api/v1/admin/auth/logout` | POST | Admin logout |
| `/api/v1/admin/auth/session` | GET | Check session status |
| `/api/v1/admin/settings/llm` | GET/PUT | LLM configuration |
| `/api/v1/admin/panel-history` | GET | Panel history list |
| `/api/v1/admin/panel-history/{id}` | GET | Panel history detail |
| `/api/v1/admin/quality-registry/*` | Various | Quality issue management |

## Usage

### AI Experimental Design

Navigate to `/exp-design` and describe your experiment:
```
I want to identify T cell subsets in human blood, including CD4+ and CD8+ populations, 
and assess their activation state and memory phenotype.
```

The AI will suggest appropriate markers and generate a panel design strategy.

### Panel Generation

Use `/panel-design` to:
1. Select target species (human/mouse)
2. Specify required markers
3. Set fluorochrome preferences
4. Generate panels with the "Generate" button
5. Review panel recommendations

### Quality Registry

Access `/quality-registry` to:
1. View existing quality records
2. Add new quality issues for antibody lots
3. Filter by marker, catalog number, or issue type
4. Export data for analysis

## Project Structure

```
PanelAgent/
├── frontend/                 # User-facing Next.js application (port 3000)
│   ├── src/
│   │   ├── app/              # App Router pages
│   │   │   ├── page.tsx              # Dashboard home
│   │   │   ├── exp-design/           # AI experimental design
│   │   │   ├── panel-design/         # Panel generation
│   │   │   └── quality-registry/     # Quality registry
│   │   ├── components/       # React components
│   │   │   ├── ui/           # shadcn/ui components
│   │   │   └── spectra-chart.tsx     # Spectral visualization
│   │   └── lib/              # Utilities and hooks
│   │       ├── api/          # OpenAPI-generated client
│   │       └── hooks/        # Custom React hooks
│   ├── public/               # Static assets
│   └── package.json
│
├── admin-frontend/           # Admin Next.js application (port 3001)
│   ├── src/
│   │   ├── app/              # App Router pages
│   │   │   ├── login/               # Admin login
│   │   │   ├── settings/            # System settings
│   │   │   ├── history/             # Panel history
│   │   │   └── quality-registry/    # Quality management
│   │   ├── components/       # Admin-specific components
│   │   └── lib/              # Admin utilities
│   └── package.json
│
├── backend/                  # FastAPI application (port 8000)
│   ├── app/
│   │   ├── api/v1/endpoints/ # API route handlers
│   │   │   ├── panels.py            # Panel operations
│   │   │   ├── quality_registry.py  # Quality CRUD
│   │   │   ├── recommendations.py   # Marker suggestions
│   │   │   └── spectra.py           # Spectral data
│   │   ├── services/         # Business logic
│   │   ├── schemas/          # Pydantic models
│   │   └── core/             # Configuration
│   └── requirements.txt
│
├── gateway/                  # Nginx reverse proxy (port 8080)
│   └── nginx.conf            # Gateway routing configuration
│
├── inventory/                # Antibody inventory CSVs
│   ├── human_inventory.csv
│   └── mouse_inventory.csv
│
├── data/                     # Static reference data
│   ├── channel_mapping.csv   # Instrument channels
│   ├── fluorochrome_brightness.csv
│   └── spectra/              # Spectral data files
│
├── docs/                     # Documentation
│   └── route-ownership-matrix.md
│
├── tests/                    # Python tests
├── docker-compose.yml        # Multi-service Docker stack
├── Dockerfile.backend        # Backend container image
├── Dockerfile.frontend       # Frontend container image (shared)
├── Makefile                  # Project commands
└── .agents/                  # Agent skill configurations
```

## API Reference

### Public API (User Frontend)

#### Panel Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/panels/generate` | POST | Generate a new panel |
| `/api/v1/panels/diagnose` | POST | Diagnose panel issues |
| `/api/v1/panels/evaluate` | POST | Evaluate panel quality |

#### Quality Registry (Public)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/quality-registry/issues` | POST | Submit a quality issue |
| `/api/v1/quality-registry/candidates/lookup` | POST | Lookup antibody candidates |
| `/api/v1/quality-registry/candidates/confirm` | POST | Confirm candidate selection |

#### Recommendations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/recommendations/markers` | POST | Get marker recommendations |

#### Spectra

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/spectra` | GET | List available spectra |
| `/api/v1/spectra/{marker}` | GET | Get specific spectrum data |

#### Health

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check |

### Admin API (Admin Frontend)

All admin endpoints require session authentication.

#### Authentication

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/admin/auth/login` | POST | Admin login |
| `/api/v1/admin/auth/logout` | POST | Admin logout |
| `/api/v1/admin/auth/session` | GET | Check session status |

#### Settings

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/admin/settings/llm` | GET | Get LLM configuration |
| `/api/v1/admin/settings/llm` | PUT | Update LLM configuration |

#### Panel History

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/admin/panel-history` | GET | List panel history entries |
| `/api/v1/admin/panel-history/{id}` | GET | Get panel history detail |

#### Quality Management

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/admin/quality-registry/issues` | GET | List all quality issues |
| `/api/v1/admin/quality-registry/issues/{id}` | GET | Get issue detail |
| `/api/v1/admin/quality-registry/issues/{id}` | PUT | Update an issue |
| `/api/v1/admin/quality-registry/issues/{id}/history` | GET | Issue audit history |
| `/api/v1/admin/quality-registry/review-queue` | GET | Get review queue |
| `/api/v1/admin/quality-registry/review-queue/{id}/resolve` | POST | Resolve an issue |

## Development

### Available Make Commands

```bash
# Dev servers
make dev-backend          # Start backend server (port 8000)
make dev-frontend         # Start user frontend (port 3000)
make dev-admin-frontend   # Start admin frontend (port 3001)
make dev-all              # Start all three services

# Quality checks
make test-backend          # Run Python tests (pytest)
make lint-backend          # Lint Python code (ruff)
make lint-frontend         # Lint user frontend TypeScript (eslint)
make lint-admin-frontend   # Lint admin frontend TypeScript (eslint)
make typecheck-frontend    # User frontend TypeScript type check
make typecheck-admin-frontend  # Admin frontend TypeScript type check
make generate-client       # Generate OpenAPI client
make e2e-frontend          # Run Playwright E2E tests
make check-all             # Run all quality gates
```

### Generating OpenAPI Client

When backend API changes, regenerate the frontend client:

```bash
make generate-client
```

This creates TypeScript types and API client from the FastAPI OpenAPI schema.

### Testing

**Backend tests:**
```bash
cd backend
pytest tests/
```

**Frontend E2E tests:**
```bash
cd frontend
npm run test:e2e
```

## Docker Deployment

### Build and Start

```bash
# Build all images
docker compose build

# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f

# Stop
docker compose down
```

### Individual Service Logs

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f admin-frontend
docker compose logs -f gateway
```

### Service Endpoints (Docker)

| Service | URL |
|---------|-----|
| User App | `http://localhost:3000` |
| Admin App | `http://localhost:3001` |
| Backend API | `http://localhost:8000` |
| Gateway (all-in-one) | `http://localhost:8080` |

### Gateway Routing

The nginx gateway on port 8080 provides unified access:
- `http://localhost:8080/` → User frontend
- `http://localhost:8080/admin/` → Admin frontend
- `http://localhost:8080/api/v1/` → Backend API (via user frontend proxy)
- `http://localhost:8080/admin/api/v1/` → Admin API (via admin frontend proxy)

## Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork and branch**: Create a feature branch from `main`
2. **Code quality**: Run `make check-all` before committing
3. **Tests**: Add tests for new functionality
4. **Documentation**: Update relevant documentation
5. **Pull request**: Submit PR with clear description

### Development Setup

1. Install development dependencies:
```bash
pip install -r backend/requirements.txt
cd frontend && npm install
cd admin-frontend && npm install
```

2. Set up pre-commit hooks (optional):
```bash
pre-commit install
```

### Code Style

- **Python**: Follow PEP 8, enforced by Ruff
- **TypeScript**: ESLint + Prettier configuration
- **Commits**: Conventional commit messages preferred

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Maintainers**: Pan Chongshi

**Acknowledgments**: 
- OpenAI for GPT API access
- shadcn/ui for excellent component library
- FastAPI and Next.js communities
