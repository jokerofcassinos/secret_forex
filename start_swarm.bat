@echo off
title NEXUS-QUANT AGI SWARM v2.0
color 0A

echo ===================================================
echo     LIMPANDO PROCESSOS FANTASMAS (PREVENCAO MEMORY LEAK)
echo ===================================================
taskkill /F /IM python.exe /T >nul 2>&1

set SYMBOL=%~1
if "%SYMBOL%"=="" set SYMBOL=GER40.cash

echo ===================================================
echo     NEXUS-QUANT :: INICIANDO ZERO-MQ SWARM
echo     ATIVO ALVO: %SYMBOL%
echo ===================================================
echo.
echo Iniciando Q-MATH Node (Calculos C++)...
start "Q-MATH NODE [%SYMBOL%]" cmd /k "python q_math_node.py"
timeout /t 2 /nobreak >nul

echo Iniciando AGI CORE (Orquestrador Neural)...
start "AGI CORE [%SYMBOL%]" cmd /k "python Aethelgard_Swarm.py --symbol %SYMBOL%"
timeout /t 2 /nobreak >nul

echo Iniciando NEXUS ROUTER (Conexao MT5 PUB/SUB)...
start "NEXUS ROUTER [%SYMBOL%]" cmd /k "python nexus_router.py --symbol %SYMBOL%"

echo.
echo ===================================================
echo Swarm Operacional! Verifique as 3 janelas do terminal.
echo ===================================================
pause
