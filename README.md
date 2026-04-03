# PanelAgent

[![Next.js](https://img.shields.io/badge/Next.js-16.2.1-black?logo=next.js)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19.2.4-61DAFB?logo=react)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python)](https://python.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--5.2-412991?logo=openai)](https://openai.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**AI-powered multi-color flow cytometry panel design tool for immunologists and flow cytometry researchers.**

PanelAgent combines deterministic algorithms with Large Language Model (LLM) evaluation to generate physically valid flow cytometry panels grounded in real antibody inventory data. It helps researchers design optimal antibody panels by considering spectral overlap, fluorochrome brightness, and experimental requirements.

## Table of Contents

- [Background](#background)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the Application](#running-the-application)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Development](#development)
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
| **Frontend** | Next.js 16.2.1, React 19.2.4, TypeScript |
| **UI Framework** | shadcn/ui (Base UI + Tailwind CSS 4) |
| **Charts** | Recharts 3.8.1 |
| **AI Integration** | Vercel AI SDK, OpenAI API |
| **Backend** | FastAPI 0.115+, Python 3.13+ |
| **Data Processing** | Pandas, NumPy, SciPy |
| **Testing** | Playwright (E2E), Pytest |

## Getting Started

### Prerequisites

- **Node.js** 18+ and npm/pnpm
- **Python** 3.13+
- **OpenAI API access** (or compatible API endpoint)

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

3. Install frontend dependencies:
```bash
cd frontend
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

# Alternative: Use a compatible API endpoint
# OPENAI_API_BASE=https://your-endpoint.com/v1
```

**Frontend (`frontend/.env.local`):**
```bash
# Backend API URL (internal)
BACKEND_INTERNAL_URL=http://127.0.0.1:8000

# Public backend URL (if different)
BACKEND_PUBLIC_URL=http://localhost:8000
```

### Running the Application

**Start the backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Start the frontend:**
```bash
cd frontend
npm run dev
```

The application will be available at `http://localhost:3000`.

**Using Make commands:**
```bash
make dev-backend    # Start backend server
make dev-frontend   # Start frontend server
make check-all       # Run all quality checks
```

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
├── frontend/                 # Next.js application
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
├── backend/                  # FastAPI application
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
├── inventory/                # Antibody inventory CSVs
│   ├── human_inventory.csv
│   └── mouse_inventory.csv
│
├── data/                     # Static reference data
│   ├── channel_mapping.csv   # Instrument channels
│   ├── fluorochrome_brightness.csv
│   └── spectra/              # Spectral data files
│
├── tests/                    # Python tests
├── Makefile                  # Project commands
└── .agents/                  # Agent skill configurations
```

## API Reference

### Panel Operations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/panels/generate` | POST | Generate a new panel |
| `/api/v1/panels/diagnose` | POST | Diagnose panel issues |
| `/api/v1/panels/evaluate` | POST | Evaluate panel quality |

### Quality Registry

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/quality-registry` | GET | List quality records |
| `/api/v1/quality-registry` | POST | Create quality record |
| `/api/v1/quality-registry/{id}` | PUT | Update quality record |
| `/api/v1/quality-registry/{id}` | DELETE | Delete quality record |
| `/api/v1/quality-registry/projection` | POST | Project quality for markers |

### Recommendations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/recommendations/markers` | POST | Get marker recommendations |

### Spectra

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/spectra` | GET | List available spectra |
| `/api/v1/spectra/{marker}` | GET | Get specific spectrum data |

## Development

### Available Make Commands

```bash
make test-backend          # Run Python tests (pytest)
make lint-backend          # Lint Python code (ruff)
make lint-frontend         # Lint TypeScript (eslint)
make typecheck-frontend    # TypeScript type check
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
pip install -r requirements.txt
npm install
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