#!/bin/bash

echo "========================================"
echo "  BTC Trader Bot V7.4"
echo "========================================"
echo ""

# Vérifier si .env existe
if [ ! -f .env ]; then
    echo "[ERREUR] Fichier .env manquant !"
    echo ""
    echo "Copiez .env.example vers .env et configurez vos credentials."
    exit 1
fi

echo "[OK] Fichier .env détecté"
echo ""

# Vérifier et installer les dépendances
echo "[INFO] Vérification des dépendances..."
python3 check_deps.py
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERREUR] Problème avec les dépendances !"
    exit 1
fi

echo "[INFO] Démarrage du bot..."
echo ""
python3 main.py
