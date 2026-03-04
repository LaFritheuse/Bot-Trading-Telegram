#!/usr/bin/env python3
"""
Script de nettoyage du projet BTC Trader Bot

Supprime tous les fichiers inutiles :
- Fichiers .pyc (bytecode compilé)
- Dossiers __pycache__
- Fichiers .log
- trades.json (données utilisateur)
- .env (credentials sensibles)
"""

import os
import shutil
from pathlib import Path

# Couleurs pour output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def clean_project():
    """Nettoie le projet de tous les fichiers inutiles"""
    
    print("🧹 NETTOYAGE DU PROJET BTC TRADER BOT")
    print("=" * 60)
    print()
    
    deleted_files = 0
    deleted_dirs = 0
    
    # 1. Supprimer les fichiers .pyc
    print("1️⃣ Suppression des fichiers .pyc...")
    for pyc_file in Path('.').rglob('*.pyc'):
        try:
            pyc_file.unlink()
            print(f"  {RED}✗{RESET} Supprimé : {pyc_file}")
            deleted_files += 1
        except Exception as e:
            print(f"  {YELLOW}⚠{RESET} Erreur : {pyc_file} - {e}")
    
    if deleted_files == 0:
        print(f"  {GREEN}✓{RESET} Aucun fichier .pyc trouvé")
    print()
    
    # 2. Supprimer les dossiers __pycache__
    print("2️⃣ Suppression des dossiers __pycache__...")
    for pycache_dir in Path('.').rglob('__pycache__'):
        try:
            shutil.rmtree(pycache_dir)
            print(f"  {RED}✗{RESET} Supprimé : {pycache_dir}")
            deleted_dirs += 1
        except Exception as e:
            print(f"  {YELLOW}⚠{RESET} Erreur : {pycache_dir} - {e}")
    
    if deleted_dirs == 0:
        print(f"  {GREEN}✓{RESET} Aucun dossier __pycache__ trouvé")
    print()
    
    # 3. Supprimer les fichiers .log
    print("3️⃣ Suppression des fichiers .log...")
    log_count = 0
    for log_file in Path('.').rglob('*.log'):
        try:
            log_file.unlink()
            print(f"  {RED}✗{RESET} Supprimé : {log_file}")
            log_count += 1
        except Exception as e:
            print(f"  {YELLOW}⚠{RESET} Erreur : {log_file} - {e}")
    
    if log_count == 0:
        print(f"  {GREEN}✓{RESET} Aucun fichier .log trouvé")
    print()
    
    # 4. Supprimer trades.json (données utilisateur)
    print("4️⃣ Suppression de trades.json...")
    trades_file = Path('trades.json')
    if trades_file.exists():
        try:
            trades_file.unlink()
            print(f"  {RED}✗{RESET} Supprimé : trades.json")
        except Exception as e:
            print(f"  {YELLOW}⚠{RESET} Erreur : {e}")
    else:
        print(f"  {GREEN}✓{RESET} trades.json n'existe pas")
    print()
    
    # 5. Supprimer .env (credentials sensibles)
    print("5️⃣ Suppression de .env...")
    env_file = Path('.env')
    if env_file.exists():
        try:
            env_file.unlink()
            print(f"  {RED}✗{RESET} Supprimé : .env")
            print(f"  {YELLOW}ℹ{RESET} Utilise .env.example comme template")
        except Exception as e:
            print(f"  {YELLOW}⚠{RESET} Erreur : {e}")
    else:
        print(f"  {GREEN}✓{RESET} .env n'existe pas")
    print()
    
    # Résumé
    print("=" * 60)
    print(f"{GREEN}✅ NETTOYAGE TERMINÉ{RESET}")
    print(f"  • Fichiers supprimés : {deleted_files + log_count + (1 if trades_file.exists() else 0)}")
    print(f"  • Dossiers supprimés : {deleted_dirs}")
    print()
    print("Le projet est maintenant propre et prêt pour le transfert ! 🎉")

if __name__ == '__main__':
    clean_project()
