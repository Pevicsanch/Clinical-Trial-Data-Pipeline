FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen

# Copy source code
COPY src/ src/
COPY sql/ sql/

# Install the package
RUN uv pip install -e .

# Create data directory
RUN mkdir -p data

ENTRYPOINT ["uv", "run", "python", "-m", "clinical_trial_pipeline.cli"]
CMD ["ingest", "--help"]
