@echo off
title NEXUS-QUANT AGI SWARM v3.0 (SINGULARITY)
color 0B

echo ===================================================
echo     LIMPANDO PROCESSOS FANTASMAS (PREVENCAO MEMORY LEAK)
echo ===================================================
taskkill /F /IM python.exe /T >nul 2>&1

set SYMBOL=%~1
if "%SYMBOL%"=="" set SYMBOL=GER40.cash

echo ===================================================
echo     NEXUS AGI CEO :: INICIANDO A MATRIX V3.0
echo     ATIVO ALVO: %SYMBOL%
echo     MOTOR FISICO: O Colisor (C++ OpenMP)
echo ===================================================
echo.

echo [1/3] Iniciando Q-MATH Node (O Colisor Matematico)...
start "Q-MATH NODE [%SYMBOL%]" cmd /k "python q_math_node.py"
timeout /t 2 /nobreak >nul

echo [2/3] Iniciando N-CORE (Cerebro Assincrono)...
start "N-CORE SWARM [%SYMBOL%]" cmd /k "python Aethelgard_Swarm.py --symbol %SYMBOL%"
timeout /t 2 /nobreak >nul

echo [3/3] Iniciando NEXUS ROUTER (Injecao Zero-MQ)...
start "NEXUS ROUTER [%SYMBOL%]" cmd /k "python nexus_router.py --symbol %SYMBOL%"

echo.
echo ===================================================
echo 🌌 SINGULARIDADE ALCANCADA! 
echo Verifique as 3 janelas do terminal. Aguardando MT5 HFT Bridge.
echo ===================================================
pause
