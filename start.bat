@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo   SearNXG - web search for humans and models
echo   ================================================
echo.

REM --- Check the two tools we need -----------------------------------------
where python >nul 2>&1
if errorlevel 1 (
  echo   Python is not installed.
  echo   Download it from https://www.python.org/downloads/
  echo   Important: tick "Add Python to PATH" during installation.
  echo   Then run this file again.
  pause
  exit /b 1
)

where npm >nul 2>&1
if errorlevel 1 (
  echo   Node.js is not installed.
  echo   Download the LTS version from https://nodejs.org/
  echo   Then run this file again.
  pause
  exit /b 1
)

REM --- Optional: the SearXNG search engine (needs Docker) ------------------
set "USE_SEARXNG=0"
where docker >nul 2>&1
if not errorlevel 1 (
  docker info >nul 2>&1
  if errorlevel 1 (
    echo   Docker is installed but not running. Trying to start it...
    if exist "%LOCALAPPDATA%\Programs\DockerDesktop\Docker Desktop.exe" (
      start "" "%LOCALAPPDATA%\Programs\DockerDesktop\Docker Desktop.exe"
      ping -n 15 127.0.0.1 >nul 2>&1
    )
    docker info >nul 2>&1
  )
  if not errorlevel 1 (
    echo.
    echo   Docker is available. You can optionally start a local SearXNG engine.
    echo   The app works fine without it, so this is your choice.
    choice /C YN /N /M "   Start the SearXNG engine too? (Y=yes, N=no, recommended: Y): "
    if errorlevel 2 (
      set "USE_SEARXNG=0"
    ) else (
      set "USE_SEARXNG=1"
    )
  ) else (
    echo   Docker is installed but could not be started. Continuing without the engine.
  )
) else (
  echo   Docker not found. No problem, the app will use its built-in sources.
  echo   Optional: Docker Desktop is ~600 MB from https://www.docker.com/products/docker-desktop/
)

if "!USE_SEARXNG!"=="1" (
  echo.
  echo   Starting SearXNG on http://localhost:8080 ...
  echo   First run downloads the engine image, so this can take a few minutes.
  docker compose up -d searxng
  if errorlevel 1 (
    echo   Could not start SearXNG. The app will still work using built-in sources.
    set "USE_SEARXNG=0"
  ) else (
    echo   SearXNG is starting on port 8080. The app will connect to it automatically.
  )
)

REM --- Pick free ports (set BACKEND_PORT / UI_PORT first to override) ------
if not defined BACKEND_PORT set BACKEND_PORT=8010
if not defined UI_PORT set UI_PORT=5174

:findBackend
netstat -ano 2>nul | findstr /r /c:":%BACKEND_PORT% .*LISTENING" >nul
if not errorlevel 1 (
  set /a BACKEND_PORT+=1
  goto findBackend
)

:findUI
netstat -ano 2>nul | findstr /r /c:":%UI_PORT% .*LISTENING" >nul
if not errorlevel 1 (
  set /a UI_PORT+=1
  goto findUI
)

REM --- Set up Python --------------------------------------------------------
if not exist ".venv\Scripts\python.exe" (
  echo.
  echo   [1/4] Setting up Python. This only happens once...
  python -m venv .venv
  if errorlevel 1 goto :failed
  ".venv\Scripts\python.exe" -m pip install --upgrade pip -q
  ".venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
  if errorlevel 1 goto :failed
) else (
  echo.
  echo   [1/4] Python is ready.
)

REM --- Set up the web interface --------------------------------------------
if not exist "frontend\node_modules" (
  echo   [2/4] Downloading the interface. This only happens once...
  pushd frontend
  call npm install
  popd
  if errorlevel 1 goto :failed
) else (
  echo   [2/4] Interface files are ready.
)

if not exist "frontend\dist\index.html" (
  echo   [3/4] Building the interface. This only happens once...
  pushd frontend
  call npm run build
  popd
  if errorlevel 1 goto :failed
) else (
  echo   [3/4] Interface is built.
)

echo   [4/4] Starting SearNXG...
echo.
echo   Web page:   http://localhost:%UI_PORT%
echo   API:        http://localhost:%BACKEND_PORT%
echo   Search engine: !USE_SEARXNG! (0 = built-in sources, 1 = local SearXNG)
echo   Help:       http://localhost:%BACKEND_PORT%/api/docs
echo.
echo   Two windows will open. Close them to stop SearNXG.
echo.

if "!USE_SEARXNG!"=="1" (
  start "SearNXG API" /D "%~dp0backend" cmd /k "set SEARXNG_URL=http://localhost:8080&& ..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
) else (
  start "SearNXG API" /D "%~dp0backend" cmd /k "..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port %BACKEND_PORT%"
)
start "SearNXG UI" /D "%~dp0frontend" cmd /k "set VITE_BACKEND_PORT=%BACKEND_PORT%&& set VITE_UI_PORT=%UI_PORT%&& npm run dev"

ping -n 6 127.0.0.1 >nul 2>&1
start "" "http://localhost:%UI_PORT%"
exit /b 0

:failed
echo.
echo   Setup did not finish. Read the error above, then try again.
pause
exit /b 1
