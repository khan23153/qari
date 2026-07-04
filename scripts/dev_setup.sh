#!/usr/bin/env bash
set -euo pipefail

echo "🚀 Setting up Qari development environment..."

# Start infra
echo "Starting PostgreSQL + Redis..."
cd infra
docker-compose up -d postgres redis minio
cd ..

# Wait for postgres
echo "Waiting for PostgreSQL..."
until docker-compose -f infra/docker-compose exec postgres pg_isready -U qari; do
  sleep 1
done

# Core API
echo "Setting up core-api..."
cd backend/core_api
pip install -r requirements.txt
alembic upgrade head
cd ../..

# Recitation API
echo "Setting up recitation-api..."
cd backend/recitation_api
pip install -r requirements.txt
cd ../..

# ETL
echo "Setting up ETL..."
cd etl
pip install -r requirements.txt
cd ..

# ML
echo "Setting up ML..."
cd ml
pip install -r requirements.txt
cd ..

echo "✅ Setup complete! Run:"
echo "  cd backend/core_api && uvicorn app.main:app --reload"
echo "  cd backend/recitation_api && uvicorn app.main:app --reload --port 8001"
echo "  cd mobile && flutter run"
