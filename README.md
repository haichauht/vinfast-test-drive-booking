# AI20K Agent Template

Template chinh thuc cho hoc vien VinUni AI20K Build Phase - cung cap cau truc du an co ban, code mau va huong dan chi tiet de xay dung AI Agent.

## 1) Mot nhanh ve du an

Du an nay la mot AI agent co ban duoc xay dung theo ki hieu:

- FastAPI backend
- LangGraph agent
- Config, schema, logging
- Docker va CI/CD tu dong
- Cai dat de ho tro nop bai AI20K

## 2) Technical Guidebook

- Chon tab AI20K Technical Book de doc chi tiet:
  https://phoenix.note.transformerlabs.ai/technical-book


## 4) Cac buoc thuc hien

### Buoc 1: Clone va khoi dong repo

```bash
git clone https://github.com/AI20K-Build-Phase-Cohort-3/starter-code-template.git
cd ten-team-cua-ban
```

### Buoc 2: Cai dat moi truong

```bash
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
# hoac
.venv\\Scripts\\activate     # Windows PowerShell

pip install -e ".[dev]"
cp .env.example .env
```

### Buoc 3: Chay local

```bash
uvicorn src.main:app --reload --port 8000
```

- Swagger: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Buoc 4: API co ban

- GET `/health`: kiem tra server hoat dong
- GET `/api/v1/status`: kiem tra trang thai agent
- POST `/api/v1/chat`: gui tin nhan den agent
- GET `/api/v1/echo?text=...`: echo thong tin kiem tra nhanh

### Buoc 5: Cau truc thu muc

```
src/
  agents/           # LangGraph Agent
    graph.py
    state.py
    nodes/
  api/
    routes.py
  models/
    schemas.py
  services/         # Business logic / LLM / tools
  config.py
  main.py

tests/
  test_agents/
  test_api/

scripts/
  log_hook.py
  log_manual.py
  log_codex_ide.py
  log_antigravity.py
  submit_log.py
  setup_hooks.sh
  setup_hooks.ps1

docs/
  guide/
  architecture_diagram.md
```

## 5) AI usage logging

He thong da co truoc:

- `.claude/settings.json`
- `.codex/hooks.json`
- `.cursor/hooks.json`
- `.gemini/settings.json`
- `.github/hooks/hooks.json`
- `.ai-log/session.jsonl` (chi de luu log)

Neu dung ChatGPT/web khong co hook tu dong, su dung:

```bash
python scripts/log_manual.py --tool chatgpt --prompt "Noi dung da hoi"
```

## 6) Cau lenh nhanh

```bash
make run      # chay uvicorn dev
make test     # chay test
make lint     # chay ruff check
make format   # format code
```

## 7) Docker va CI/CD

- Build/run Docker:

```bash
docker compose up --build
```

- CI workflow:
  - lint: `ruff check`
  - test: `pytest`

## 8) Quan trong

- Khong commit `.env`
- Kiem tra `.gitignore` truoc khi commit
- Cap nhat thong tin nhom va MSSV trong file nay
- Chi sua code phu hop voi mo hinh AI20K cua nhom

## 9) License

MIT

