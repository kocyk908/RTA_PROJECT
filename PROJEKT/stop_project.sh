#!/bin/bash

echo "=========================================="
echo "ZATRZYMYWANIE PROJEKTU"
echo "=========================================="

echo " Zamykam procesy uvicorn..."
pkill -f uvicorn

echo " Zamykam procesy python (konsumenci, producer)..."
pkill -f "python producer.py"
pkill -f "python consumer_rules.py"
pkill -f "python consumer_ml.py"

echo ""
echo " Wszystkie procesy zatrzymane"
echo "=========================================="