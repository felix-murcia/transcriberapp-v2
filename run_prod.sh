#!/bin/bash
set -e
cd "$(dirname "$0")"

COMPOSE="docker compose -f docker-compose.yml"

case "${1:-up}" in
  up)
    # Detener entorno DEV si está corriendo para evitar conflictos de red
    if docker compose -f docker-compose.dev.yml ps --quiet 2>/dev/null | grep -q .; then
      echo "[!] Deteniendo entorno DEV antes de arrancar PROD..."
      docker compose -f docker-compose.dev.yml down
    fi
    $COMPOSE down --remove-orphans
    (cd frontend && npm run build --silent)
    $COMPOSE up -d --build
    ;;
  down)
    $COMPOSE down
    ;;
  restart)
    $COMPOSE down
    (cd frontend && npm run build --silent)
    $COMPOSE up -d --build
    ;;
  logs)
    $COMPOSE logs -f backend
    ;;
  *)
    echo "Uso: $0 [up|down|restart|logs]"
    exit 1
    ;;
esac
