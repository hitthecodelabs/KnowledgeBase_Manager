#!/bin/bash

echo "======================================"
echo "Vector Store Platform - Backend"
echo "======================================"
echo ""

# Verificar si Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 no está instalado"
    exit 1
fi

# Verificar si las dependencias están instaladas
echo "Verificando dependencias..."
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "Instalando dependencias..."
    pip install -r requirements.txt
fi

echo ""
echo "Iniciando servidor backend en http://localhost:8000"
echo "Presiona Ctrl+C para detener"
echo ""

# Iniciar servidor
python3 api.py
