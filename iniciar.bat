@echo off
echo =====================================================
echo   ----------------NOTA FISCAL------------------------
echo =====================================================
echo.

REM Verifica se o arquivo .env existe
if not exist ".env" (
    echo ERRO: Arquivo .env não encontrado!
    echo Por favor, configure suas variáveis de ambiente primeiro.
    echo.
    echo 1. Crie o arquivo .env na raiz do projeto
    echo 2. Adicione sua chave do Gemini: GEMINI_API_KEY=sua_chave_aqui
    echo.
    pause
    exit /b 1
)

REM Verifica se o ambiente virtual existe
if not exist ".venv\" (
    echo ERRO: Ambiente virtual não encontrado!
    echo Execute: python -m venv .venv
    pause
    exit /b 1
)

echo Iniciando servidor Django...
echo.
echo Interface web disponível em: http://127.0.0.1:8000/
echo.

REM Define variável de ambiente e roda o servidor
set DJANGO_SETTINGS_MODULE=nfe_project.settings
.venv\Scripts\python.exe manage.py runserver