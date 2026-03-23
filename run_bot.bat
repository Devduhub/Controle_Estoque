@echo off
echo ========================================
echo   BOT ANTISHOCK ESTOQUE
echo ========================================
echo.

REM Carrega variáveis do arquivo .env
if not exist .env (
    echo [ERRO] Arquivo .env nao encontrado!
    echo Copie o .env.example para .env e preencha seus tokens.
    pause
    exit /b 1
)

echo [*] Carregando variaveis do .env...
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if not "%%A"=="" if not "%%A:~0,1%"=="#" (
        set "%%A=%%B"
    )
)
echo [OK] Variaveis carregadas

echo.
echo [*] Instalando dependencias...
"C:\.....\....\AppData\Local\Programs\Python\Python311\python.exe" -m pip install -q -r requirements.txt
echo [OK] Dependencias prontas

echo.
echo [*] Iniciando BOT...
echo.
"C:\.....\......\AppData\Local\Programs\Python\Python311\python.exe" bot_telegram.py
pause