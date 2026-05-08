@echo off
setlocal EnableDelayedExpansion
title NEXUS-QUANT AGI SWARM v3.0 (SINGULARITY)
color 0B

echo ===================================================
echo     LIMPANDO PROCESSOS FANTASMAS (PREVENCAO MEMORY LEAK)
echo ===================================================
taskkill /F /IM python.exe /T >nul 2>&1

echo ===================================================
echo     NEXUS AGI CEO :: MATRIZ DE DECOLAGEM
echo ===================================================
echo.
set /p SYMBOL="[INPUT] Digite o Ativo Alvo (Ex: GER40.cash, US100.cash) [Enter para GER40.cash]: "
if "!SYMBOL!"=="" set SYMBOL=GER40.cash

echo.
echo ===================================================
echo     INICIANDO A MATRIX V3.0 PARA: !SYMBOL!
echo     MOTOR FISICO: O Colisor (C++ OpenMP)
echo ===================================================
echo.

echo [1/3] Iniciando Q-MATH Node (O Colisor Matematico)...
start "Q-MATH NODE [!SYMBOL!]" cmd /c "title Q-MATH NODE && python q_math_node.py"
timeout /t 2 /nobreak >nul

echo [2/3] Iniciando N-CORE (Cerebro Assincrono)...
start "N-CORE SWARM [!SYMBOL!]" cmd /c "title N-CORE SWARM && python Aethelgard_Swarm.py --symbol !SYMBOL!"
timeout /t 2 /nobreak >nul

echo [3/3] Iniciando NEXUS ROUTER (Injecao Zero-MQ)...
start "NEXUS ROUTER [!SYMBOL!]" cmd /c "title NEXUS ROUTER && python nexus_router.py --symbol !SYMBOL!"

echo.
echo ===================================================
echo 🌌 SINGULARIDADE ALCANCADA! 
echo O Swarm esta operando nas 3 janelas abertas.
echo.
echo [ATENCAO] PARA DESLIGAR O ROBO COM SEGURANCA:
echo Feche ESTA janela principal e o Windows matara a IA.
echo ===================================================

:: Mantem o script rodando de forma ociosa esperando fechar
:LOOP
timeout /t 10 >nul
goto LOOP

:: Trata o fechamento ou interrupcao (Ctrl+C)
:END
echo.
echo Desligando Swarm...
taskkill /F /FI "WINDOWTITLE eq Q-MATH NODE*" /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq N-CORE SWARM*" /T >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq NEXUS ROUTER*" /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1
exit

