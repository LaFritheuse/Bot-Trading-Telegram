# 📂 GUIDE DE RECONSTRUCTION MANUELLE DU PROJET

Si tu dois copier-coller les fichiers un par un, suis ce guide étape par étape.

---

## 🎯 OBJECTIF

Recréer cette structure :
```
btc_bot_final/
├── strategies/
├── ui/
├── handlers/
├── docs/
└── [fichiers racine]
```

---

## 📋 ÉTAPE 1 : CRÉER LES DOSSIERS

Crée **4 dossiers** vides dans `btc_bot_final/` :

```
✅ Créer : btc_bot_final/strategies/
✅ Créer : btc_bot_final/ui/
✅ Créer : btc_bot_final/handlers/
✅ Créer : btc_bot_final/docs/
```

Tu devrais avoir maintenant :
```
btc_bot_final/
├── strategies/     ← Dossier vide
├── ui/             ← Dossier vide
├── handlers/       ← Dossier vide
└── docs/           ← Dossier vide
```

---

## 📋 ÉTAPE 2 : FICHIERS RACINE (13 fichiers)

Copie ces fichiers **directement dans `btc_bot_final/`** (PAS dans un sous-dossier) :

```
📄 À LA RACINE de btc_bot_final/ :

1.  __init__.py               (fichier vide ou presque vide)
2.  main.py                   (point d'entrée du bot)
3.  config.py                 (configuration globale)
4.  database.py               (gestion trades.json)
5.  trading.py                (moteur trading temps réel)
6.  backtest.py               (backtest LONG)
7.  backtest_short.py         (backtest SHORT)
8.  backtest_rsi.py           (backtest RSI)
10. check_deps.py             (vérification dépendances)
11. clean_project.py          (script nettoyage)
12. requirements.txt          (dépendances pip)
13. README.md                 (documentation utilisateur)
14. INSTALLATION.md           (guide installation)
15. .env.example              (template configuration)
16. .gitignore                (config Git)
17. run.sh                    (script Linux/Mac)
18. run.bat                   (script Windows)
```

**Vérification :** Tu devrais avoir **18 fichiers** à la racine.

---

## 📋 ÉTAPE 3 : DOSSIER strategies/ (4 fichiers)

Copie ces fichiers **dans `btc_bot_final/strategies/`** :

```
📁 btc_bot_final/strategies/

1. __init__.py               (fichier vide)
2. sniper_v11.py             (stratégie LONG)
3. sniper_short_v11.py       (stratégie SHORT)
4. rsi_bollinger_15m.py      (stratégie RSI)
```

**Vérification :** Tu devrais avoir **4 fichiers** dans `strategies/`.

---

## 📋 ÉTAPE 4 : DOSSIER ui/ (3 fichiers)

Copie ces fichiers **dans `btc_bot_final/ui/`** :

```
📁 btc_bot_final/ui/

1. __init__.py               (fichier vide)
2. keyboards.py              (boutons Telegram)
3. messages.py               (textes interface)
```

**Vérification :** Tu devrais avoir **3 fichiers** dans `ui/`.

---

## 📋 ÉTAPE 5 : DOSSIER handlers/ (3 fichiers)

Copie ces fichiers **dans `btc_bot_final/handlers/`** :

```
📁 btc_bot_final/handlers/

1. __init__.py               (fichier vide)
2. commands.py               (commandes /start, /stop)
3. callbacks.py              (27 handlers - GROS fichier 31 KB)
```

**Vérification :** Tu devrais avoir **3 fichiers** dans `handlers/`.

---

## 📋 ÉTAPE 6 : DOSSIER docs/ (6 fichiers)

Copie ces fichiers **dans `btc_bot_final/docs/`** :

```
📁 btc_bot_final/docs/

1. README_AI.md              (guide rapide pour IA)
2. TRANSFER_TO_AI.md         (guide transfert)
3. ARCHITECTURE.md           (structure projet)
4. STRATEGIES.md             (détails stratégies)
5. CHANGELOG.md              (historique avec dates)
6. BUGS.md                   (bugs corrigés)
```

**Vérification :** Tu devrais avoir **6 fichiers** dans `docs/`.

---

## ✅ ÉTAPE 7 : VÉRIFICATION FINALE

### Structure complète attendue :

```
btc_bot_final/
│
├── strategies/              ← 4 fichiers
│   ├── __init__.py
│   ├── sniper_v11.py
│   ├── sniper_short_v11.py
│   └── rsi_bollinger_15m.py
│
├── ui/                      ← 3 fichiers
│   ├── __init__.py
│   ├── keyboards.py
│   └── messages.py
│
├── handlers/                ← 3 fichiers
│   ├── __init__.py
│   ├── commands.py
│   └── callbacks.py
│
├── docs/                    ← 6 fichiers
│   ├── README_AI.md
│   ├── TRANSFER_TO_AI.md
│   ├── ARCHITECTURE.md
│   ├── STRATEGIES.md
│   ├── CHANGELOG.md
│   └── BUGS.md
│
└── [RACINE]                 ← 18 fichiers
    ├── __init__.py
    ├── main.py
    ├── config.py
    ├── database.py
    ├── trading.py
    ├── backtest.py
    ├── backtest_short.py
    ├── backtest_rsi.py
    ├── check_deps.py
    ├── clean_project.py
    ├── requirements.txt
    ├── README.md
    ├── INSTALLATION.md
    ├── .env.example
    ├── .gitignore
    ├── run.sh
    └── run.bat
```

### Checklist de vérification :

```
✅ Dossier strategies/ existe avec 4 fichiers
✅ Dossier ui/ existe avec 3 fichiers
✅ Dossier handlers/ existe avec 3 fichiers
✅ Dossier docs/ existe avec 6 fichiers
✅ 18 fichiers à la racine de btc_bot_final/
✅ TOTAL : 34 fichiers (4+3+3+6+18)
```

---

## 🔢 COMPTAGE RAPIDE

Pour vérifier rapidement :

| Emplacement | Nombre de fichiers |
|-------------|-------------------|
| strategies/ | 4 |
| ui/ | 3 |
| handlers/ | 3 |
| docs/ | 6 |
| racine | 18 |
| **TOTAL** | **34 fichiers** |

---

## 📝 LISTE ALPHABÉTIQUE DE TOUS LES FICHIERS

Si tu veux cocher au fur et à mesure :

### Fichiers racine (btc_bot_final/)
- [ ] .env.example
- [ ] .gitignore
- [ ] __init__.py
- [ ] backtest.py
- [ ] backtest_rsi.py
- [ ] backtest_short.py
- [ ] check_deps.py
- [ ] clean_project.py
- [ ] config.py
- [ ] database.py
- [ ] INSTALLATION.md
- [ ] main.py
- [ ] README.md
- [ ] requirements.txt
- [ ] run.bat
- [ ] run.sh
- [ ] trading.py

### strategies/ (btc_bot_final/strategies/)
- [ ] __init__.py
- [ ] rsi_bollinger_15m.py
- [ ] sniper_short_v11.py
- [ ] sniper_v11.py

### ui/ (btc_bot_final/ui/)
- [ ] __init__.py
- [ ] keyboards.py
- [ ] messages.py

### handlers/ (btc_bot_final/handlers/)
- [ ] __init__.py
- [ ] callbacks.py
- [ ] commands.py

### docs/ (btc_bot_final/docs/)
- [ ] ARCHITECTURE.md
- [ ] BUGS.md
- [ ] CHANGELOG.md
- [ ] README_AI.md
- [ ] STRATEGIES.md
- [ ] TRANSFER_TO_AI.md

---

## 🚨 ERREURS FRÉQUENTES À ÉVITER

### ❌ ERREUR 1 : Fichier au mauvais endroit
```
❌ btc_bot_final/strategies/sniper_v11/sniper_v11.py  (trop profond !)
✅ btc_bot_final/strategies/sniper_v11.py             (correct)
```

### ❌ ERREUR 2 : Oublier les __init__.py
Chaque dossier (strategies/, ui/, handlers/) DOIT avoir un `__init__.py` !

### ❌ ERREUR 3 : Mauvais nom de dossier
```
❌ btc_bot_final/strategy/     (sans 's')
✅ btc_bot_final/strategies/   (avec 's')
```

### ❌ ERREUR 4 : Fichier docs/ à la racine
```
❌ btc_bot_final/README_AI.md          (mauvais !)
✅ btc_bot_final/docs/README_AI.md     (correct !)
```

---

## 🎯 ORDRE RECOMMANDÉ DE COPIE

Pour éviter les erreurs, suis cet ordre :

### 1️⃣ Créer la structure
```
1. Créer btc_bot_final/
2. Créer btc_bot_final/strategies/
3. Créer btc_bot_final/ui/
4. Créer btc_bot_final/handlers/
5. Créer btc_bot_final/docs/
```

### 2️⃣ Copier les __init__.py (fichiers vides)
```
6. Copier __init__.py dans btc_bot_final/
7. Copier __init__.py dans strategies/
8. Copier __init__.py dans ui/
9. Copier __init__.py dans handlers/
```

### 3️⃣ Copier les fichiers principaux (racine)
```
10-27. Copier les 18 fichiers restants à la racine
```

### 4️⃣ Copier strategies/
```
28-30. Copier les 3 fichiers .py dans strategies/
```

### 5️⃣ Copier ui/
```
31-32. Copier keyboards.py et messages.py dans ui/
```

### 6️⃣ Copier handlers/
```
33-34. Copier callbacks.py et commands.py dans handlers/
```

### 7️⃣ Copier docs/
```
35-40. Copier les 6 fichiers .md dans docs/
```

---

## 🔍 COMMANDES DE VÉRIFICATION

Si tu es sous Linux/Mac/Windows avec Git Bash :

### Compter les fichiers
```bash
# À la racine
ls btc_bot_final/*.* | wc -l
# Devrait afficher : 18

# Dans strategies/
ls btc_bot_final/strategies/*.py | wc -l
# Devrait afficher : 4

# Dans ui/
ls btc_bot_final/ui/*.py | wc -l
# Devrait afficher : 3

# Dans handlers/
ls btc_bot_final/handlers/*.py | wc -l
# Devrait afficher : 3

# Dans docs/
ls btc_bot_final/docs/*.md | wc -l
# Devrait afficher : 6
```

### Afficher la structure
```bash
tree btc_bot_final/
# Ou si tree n'est pas installé :
find btc_bot_final -type f | sort
```

---

## 📧 CONTENU DES __init__.py

Les fichiers `__init__.py` peuvent être **VIDES** ou contenir juste un commentaire :

```python
# __init__.py pour btc_bot_final/strategies/
"""
Stratégies de trading
"""

# __init__.py pour btc_bot_final/ui/
"""
Interface utilisateur Telegram
"""

# __init__.py pour btc_bot_final/handlers/
"""
Gestionnaires d'événements Telegram
"""
```

**Important :** Ces fichiers peuvent être complètement vides (0 octets), Python s'en fiche !

---

## ✅ APRÈS LA RECONSTRUCTION

Une fois tous les fichiers copiés :

### 1. Vérifier la syntaxe Python
```bash
cd btc_bot_final
python3 -m py_compile *.py
python3 -m py_compile strategies/*.py
python3 -m py_compile ui/*.py
python3 -m py_compile handlers/*.py
```

Si aucune erreur : ✅ Tout est bon !

### 2. Compter les fichiers
```bash
find . -type f -name "*.py" | wc -l
# Devrait afficher : 20

find . -type f -name "*.md" | wc -l
# Devrait afficher : 8 (6 dans docs/ + README.md + INSTALLATION.md)
```

### 3. Vérifier la structure
```bash
ls -R
# Doit montrer les 4 dossiers + tous les fichiers
```

---

## 🎉 TU AS FINI !

Si toutes les vérifications passent :
✅ Structure correcte
✅ 34 fichiers au bon endroit
✅ Syntaxe Python OK

→ **Le projet est prêt à être transféré à l'autre Claude !**

---

## 📤 POUR TRANSFÉRER À CLAUDE

Maintenant que tu as reconstruit le projet :

1. **Zippe le dossier** `btc_bot_final/`
2. **Upload** le ZIP à Claude
3. **Copie le prompt** de `docs/TRANSFER_TO_AI.md`
4. **Go !** 🚀

---

**Version :** 7.4 FINAL  
**Date :** 11 Février 2026  
**Auteur :** Mec + Claude
