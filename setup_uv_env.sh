#!/bin/bash

# Installer uv si ce n'est pas déjà fait
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Supprimer l'ancien venv s'il existe
rm -rf .venv

# Créer un nouveau venv avec uv
uv venv

# Activer le venv
source .venv/bin/activate

# Installer les dépendances avec uv
uv pip install -e .
