@echo off
echo.
echo  ===================================================
echo   Macaco Cidadão — Setup do ambiente local (Windows)
echo  ===================================================
echo.

:: Criar virtualenv se não existir
if not exist ".venv" (
    echo [1/3] Criando virtualenv...
    python -m venv .venv
) else (
    echo [1/3] Virtualenv já existe. Pulando criação.
)

:: Instalar dependências
echo [2/3] Instalando dependências...
.venv\Scripts\pip install -r requirements.txt

:: Criar .env se não existir
if not exist ".env" (
    echo [3/3] Criando .env a partir do exemplo...
    copy .env.example .env
    echo.
    echo  ATENÇÃO: Edite o arquivo .env com seus tokens antes de rodar.
    echo.
) else (
    echo [3/3] .env já existe. Pulando.
)

echo.
echo  ===================================================
echo   Setup concluído.
echo.
echo   Para rodar o painel de moderação:
echo     .venv\Scripts\python run_panel.py
echo     Acesse: http://localhost:5000
echo.
echo   Para rodar o bot Telegram (em outro terminal):
echo     .venv\Scripts\python run_bot.py
echo.
echo   Para importar vereadores reais (TSE 2024):
echo     .venv\Scripts\python scripts\seed_vereadores.py data\vereadores_bh_exemplo.json
echo  ===================================================
echo.
pause
