@echo off
setlocal enabledelayedexpansion
title [NEXUS EXECUTIVE TERMINAL]

:MENU
cls
echo ============================================================
echo      🌌 AETHELGARD QUANTUM SWARM :: EXECUTIVE TERMINAL
echo ============================================================
echo.
set /p ASSET=" > Digite o Ativo (ex: BTCUSD, GER40, US30): "
if "%ASSET%"=="" goto MENU

echo.
echo [1/3] Inicializando Matriz de Dados (Nexus Router)...
start "AETHELGARD_ROUTER" /min cmd /k "D:\Python313\python.exe nexus_router.py --asset %ASSET%"

timeout /t 2 >nul
echo [2/3] Inicializando Colisor de Hadrons (Q-Math Node)...
start "AETHELGARD_QMATH" /min cmd /k "D:\Python313\python.exe q_math_node.py"

timeout /t 3 >nul
echo [3/3] Inicializando Cerebro Neural (N-Core Swarm)...
start "AETHELGARD_SWARM" cmd /k "D:\Python313\python.exe Aethelgard_Swarm.py --asset %ASSET%"

echo.
echo ============================================================
echo    SISTEMA ONLINE NO ATIVO: %ASSET%
echo    Pressione QUALQUER TECLA para ENCERRAR e trocar de ativo
echo ============================================================
pause >nul

echo.
echo [!] Iniciando Protocolo de Limpeza...
taskkill /F /FI "WINDOWTITLE eq AETHELGARD_*" /T >nul 2>&1
taskkill /F /IM python.exe /FI "WINDOWTITLE eq AETHELGARD_*" /T >nul 2>&1

echo [!] Memoria Purificada.
timeout /t 2 >nul
goto MENU
