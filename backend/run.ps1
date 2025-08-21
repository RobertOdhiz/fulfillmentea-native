$env:PYTHONUTF8=1
$VENV_PATH = "backend\.venv"
if (-Not (Test-Path $VENV_PATH)) {
  python -m venv $VENV_PATH
}
& "$VENV_PATH\Scripts\pip.exe" install -U pip
& "$VENV_PATH\Scripts\pip.exe" install -r backend\requirements.txt
$env:PYTHONPATH = "backend"
& "$VENV_PATH\Scripts\python.exe" -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
