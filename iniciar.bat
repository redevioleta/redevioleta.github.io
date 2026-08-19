@echo off
title Rede Violeta — Backend
echo.
echo  ========================================
echo   Rede Violeta — Iniciando o servidor...
echo  ========================================
echo.

cd /d "%~dp0backend"

echo  [1/3] Preparando o banco de dados...
python seed.py

echo  [2/3] Subindo o backend...
start "" cmd /k "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo  Aguardando o servidor iniciar...
timeout /t 3 /nobreak >nul

echo  [3/3] Abrindo o site...
start "" "http://127.0.0.1:8000/"

echo.
echo  Servidor rodando em http://localhost:8000
echo  Site aberto no navegador!
echo.
echo  Para encerrar o servidor, feche a janela preta do backend.
echo.
pause
