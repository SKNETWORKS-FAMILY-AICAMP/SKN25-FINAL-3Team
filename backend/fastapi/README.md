# FastAPI Backend

특허 Agent Service의 API 서버 위치입니다.

```text
backend/fastapi/app/
  main.py                 FastAPI 앱 진입점
  routers/pipeline.py     pipeline run/continue API
```

기본 확인:

```bash
PYTHONPATH=. python -m compileall agents backend/fastapi/app
PYTHONPATH=. python - <<'PY'
from backend.fastapi.app.main import app
print(app.title)
PY
```

실행 예시:

```bash
PYTHONPATH=. uvicorn backend.fastapi.app.main:app --reload
```
