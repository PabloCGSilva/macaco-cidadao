#!/usr/bin/env bash
set -e

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  .env criado a partir de .env.example — preencha as variáveis obrigatórias antes de executar."
fi

echo ""
echo "✅ Ambiente configurado!"
echo ""
echo "   Ative o venv: source .venv/bin/activate"
echo "   Painel web:   python panel/app.py"
echo "   Bot Telegram: python main.py"
echo "   Testes:       pytest tests/ -v"
