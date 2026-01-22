# Clinical Trial Data Pipeline

ELT data pipeline that ingests clinical trial data from ClinicalTrials.gov API, transforming it into analytics-ready datasets.

## Overview

This project demonstrates a production-inspired data pipeline architecture for processing clinical trial data. It follows modern data engineering practices with a focus on reproducibility, data quality, and clear separation of concerns.

## Architecture

The pipeline implements an **ELT (Extract-Load-Transform)** pattern with three layers:

| Layer | Purpose |
|-------|---------|
| **Raw** | Preserve original API responses without modification |
| **Staging** | Cleaned and normalized data with quality validations |
| **Analytics** | Aggregated metrics and dimensional models |

### Data Source

- [ClinicalTrials.gov API v2](https://clinicaltrials.gov/api/v2/studies)

## Project Structure

```
├── src/clinical_trial_pipeline/
│   ├── api/            # API client
│   ├── storage/        # Database connections
│   ├── transforms/     # Data transformations
│   ├── models/         # Data schemas
│   └── core/           # Configuration
├── sql/
│   ├── raw/            # Bronze layer DDL
│   ├── staging/        # Silver transformations
│   └── analytics/      # Analytical queries
└── tests/
```

## Setup

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)

### Installation

```bash
git clone <repository-url>
cd Clinical-Trial-Data-Pipeline
uv sync
```

## Design Decisions

*To be documented as the project evolves.*
