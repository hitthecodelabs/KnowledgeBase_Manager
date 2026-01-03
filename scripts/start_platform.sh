#!/bin/bash

echo "======================================"
echo "Vector Store Platform"
echo "Iniciando Backend y Frontend"
echo "======================================"
echo ""

# Función para limpiar procesos al salir
cleanup() {
    echo ""
    echo "Deteniendo servicios..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Iniciar backend en segundo plano
echo "Iniciando Backend..."
python3 api.py &
BACKEND_PID=$!

# Esperar 3 segundos para que el backend inicie
sleep 3

# Iniciar frontend en segundo plano
echo "Iniciando Frontend..."
cd frontend && npm run dev &
FRONTEND_PID=$!

echo ""
echo "======================================"
echo "Servicios iniciados:"
echo "  Backend:  http://localhost:8000"
echo "  Frontend: http://localhost:3000"
echo "======================================"
echo ""
echo "Abre http://localhost:3000 en tu navegador"
echo "Presiona Ctrl+C para detener todos los servicios"
echo ""

# Esperar a que alguno de los procesos termine
wait
