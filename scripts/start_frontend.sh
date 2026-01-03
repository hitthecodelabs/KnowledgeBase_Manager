#!/bin/bash

echo "======================================"
echo "Vector Store Platform - Frontend"
echo "======================================"
echo ""

# Verificar si Node.js está instalado
if ! command -v node &> /dev/null; then
    echo "Error: Node.js no está instalado"
    exit 1
fi

# Navegar al directorio frontend
cd frontend

# Verificar si node_modules existe
if [ ! -d "node_modules" ]; then
    echo "Instalando dependencias..."
    npm install
fi

echo ""
echo "Iniciando servidor frontend en http://localhost:3000"
echo "Presiona Ctrl+C para detener"
echo ""

# Iniciar servidor
npm run dev
