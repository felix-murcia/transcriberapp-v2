#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

COMPOSE="docker compose -f docker-compose.yml"

echo "=== TranscriberApp PROD ==="
echo "  Frontend: http://localhost (puerto 80)"
echo "  Backend:  http://localhost:8002"
echo "  DB:       transcriberapp (postgres_data)"
echo ""

# Parar entorno DEV si está corriendo para evitar conflictos de red
if docker compose -f docker-compose.dev.yml ps --quiet 2>/dev/null | grep -q .; then
  echo "[!] Deteniendo entorno DEV antes de arrancar PROD..."
  docker compose -f docker-compose.dev.yml down
fi

# Construir frontend
echo "[1/3] Construyendo frontend..."
(cd frontend && npm run build --silent)

# Construir imágenes backend
echo "[2/3] Construyendo imágenes..."
$COMPOSE build backend

# Arrancar servicios
echo "[3/3] Arrancando servicios..."
$COMPOSE up -d

echo ""
echo "Servicios arrancados. Logs:"
$COMPOSE ps
echo ""
echo "Para ver logs: docker compose -f docker-compose.yml logs -f backend"
echo "Para parar:    ./stop-prod.sh  o  docker compose -f docker-compose.yml down"
