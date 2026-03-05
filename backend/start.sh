#!/usr/bin/env bash
# Start the Uvicorn server, binding to the dynamically assigned PORT (or 8000 as fallback)
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
