#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

COMPOSE="docker compose -f docker-compose.dev.yml"

echo "=== TranscriberApp DEV ==="
echo "  Backend:  http://localhost:8003"
echo "  Frontend: http://localhost:8088"
echo "  DB:       transcriberapp_dev (postgres_data_dev)"
echo ""

# Parar entorno PROD si está corriendo para evitar conflictos de red
if docker compose -f docker-compose.yml ps --quiet 2>/dev/null | grep -q .; then
  echo "[!] Deteniendo entorno PROD antes de arrancar DEV..."
  docker compose -f docker-compose.yml down
fi

# Construir frontend
echo "[1/3] Construyendo frontend..."
(cd frontend && npm run build --silent)

# Construir imagen backend (solo si hay cambios en Dockerfile o requirements)
echo "[2/3] Construyendo imagen backend..."
$COMPOSE build backend

# Arrancar servicios
echo "[3/3] Arrancando servicios..."
$COMPOSE up -d

echo ""
echo "Servicios arrancados. Logs:"
$COMPOSE ps
echo ""
echo "Para ver logs: docker compose -f docker-compose.dev.yml logs -f backend"
echo "Para parar:    ./stop-dev.sh  o  docker compose -f docker-compose.dev.yml down"
