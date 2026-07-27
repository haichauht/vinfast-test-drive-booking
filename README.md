# ðŸ¤– AI20K Agent Template

Template chÃ­nh thá»©c cho há»c viÃªn **VinUni AI20K Build Phase** â€” cung cáº¥p sáºµn cáº¥u trÃºc dá»± Ã¡n, code máº«u, vÃ  hÆ°á»›ng dáº«n ká»¹ thuáº­t chi tiáº¿t Ä‘á»ƒ xÃ¢y dá»±ng AI Agent Ä‘áº¡t Ä‘iá»ƒm cao (35+/50).

> ðŸ“– **Technical Guidebook:** [phoenix.note.transformerlabs.ai/technical-book](https://phoenix.note.transformerlabs.ai/technical-book)

## 👥 Danh sách thành viên

| Vai trò | Họ tên | MSSV |
|---------|--------|------|
| Team lead | [Tên] | [MSSV] |
| Thành viên | [Tên] | [MSSV] |
| Thành viên | [Tên] | [MSSV] |
| Thành viên | [Tên] | [MSSV] |

## ðŸŽ¯ Template nÃ y dÃ¹ng Ä‘á»ƒ lÃ m gÃ¬?

Khi tham gia AI20K Build Phase, má»—i Ä‘á»™i cáº§n xÃ¢y dá»±ng má»™t AI Agent hoÃ n chá»‰nh â€” tá»« kiáº¿n trÃºc, code, test, Ä‘áº¿n deploy. Thay vÃ¬ báº¯t Ä‘áº§u tá»« con sá»‘ khÃ´ng, template nÃ y cung cáº¥p:

- **Cáº¥u trÃºc thÆ° má»¥c chuáº©n** â€” Ä‘Ã£ Ä‘Æ°á»£c thiáº¿t káº¿ theo best practices (separation of concerns)
- **Code máº«u** cho cÃ¡c pháº§n cá»‘t lÃµi: LangGraph agent, FastAPI API, config, schemas
- **Docker + CI/CD sáºµn** â€” Dockerfile multi-stage, GitHub Actions workflow
- **HÆ°á»›ng dáº«n ká»¹ thuáº­t 10 chÆ°Æ¡ng** â€” tá»« clone template Ä‘áº¿n ná»™p bÃ i Demo Day
- **Checklist 10 deliverables** â€” Ä‘áº£m báº£o khÃ´ng bá» sÃ³t yÃªu cáº§u BTC
- **AI Usage Logging tá»± Ä‘á»™ng** â€” Pre-configured hooks cho Claude Code, Cursor, Codex, Gemini CLI, Antigravity, vÃ  GitHub Copilot

## âš¡ Quick Start

### BÆ°á»›c 1: Fork hoáº·c Clone

```bash
# Clone template
git clone https://github.com/AI20K-Build-Cohort-2/starter-code-template.git team-YOUR_TEAM_NAME
cd team-YOUR_TEAM_NAME

# XÃ³a git history cÅ© vÃ  khá»Ÿi táº¡o láº¡i
rm -rf .git
git init
git add .
git commit -m "feat: khá»Ÿi táº¡o dá»± Ã¡n tá»« template"
```

### BÆ°á»›c 2: Setup mÃ´i trÆ°á»ng

```bash
# Táº¡o virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# CÃ i dependencies
pip install -e ".[dev]"

# Cáº¥u hÃ¬nh API keys
cp .env.example .env
# Má»Ÿ .env vÃ  thÃªm OPENAI_API_KEY cá»§a báº¡n
# Äá»“ng thá»i cáº­p nháº­t AI_LOG_API_KEY báº±ng key riÃªng tá»« link má»i cá»§a BTC
# (giÃ¡ trá»‹ trong .env.example chá»‰ lÃ  placeholder)
```

### BÆ°á»›c 3: CÃ i AI Logging Hooks

```bash
# Linux / macOS / Git Bash
bash scripts/setup_hooks.sh

# Windows PowerShell
# powershell -ExecutionPolicy Bypass -File scripts\setup_hooks.ps1
```

Hooks tá»± Ä‘á»™ng log má»i AI prompt khi dÃ¹ng Claude Code, Cursor, Codex, Gemini CLI, Antigravity, hoáº·c GitHub Copilot. KhÃ´ng cáº§n thao tÃ¡c thá»§ cÃ´ng.

### BÆ°á»›c 4: Cháº¡y server

```bash
# Cháº¡y FastAPI backend
uvicorn src.main:app --reload --port 8000

# Má»Ÿ Swagger UI
# http://localhost:8000/docs
```

### BÆ°á»›c 5: Äá»c hÆ°á»›ng dáº«n

ðŸ“– Má»Ÿ **[Technical Guidebook](https://phoenix.note.transformerlabs.ai/technical-book)** vÃ  lÃ m theo tá»«ng chÆ°Æ¡ng.

## ðŸ“ Cáº¥u trÃºc dá»± Ã¡n

```
â”œâ”€â”€ src/
â”‚   â”œâ”€â”€ agents/           # ðŸ§  LangGraph Agent
â”‚   â”‚   â”œâ”€â”€ graph.py      #    State graph (nodes + edges)
â”‚   â”‚   â”œâ”€â”€ state.py      #    State schema (TypedDict)
â”‚   â”‚   â”œâ”€â”€ nodes/        #    Node functions
â”‚   â”‚   â””â”€â”€ tools/        #    Agent tools (@tool)
â”‚   â”œâ”€â”€ api/              # ðŸŒ FastAPI Backend
â”‚   â”‚   â””â”€â”€ routes.py     #    API endpoints
â”‚   â”œâ”€â”€ models/           # ðŸ“‹ Pydantic schemas
â”‚   â”œâ”€â”€ services/         # ðŸ”§ Business logic (LLM, etc.)
â”‚   â”œâ”€â”€ config.py         # âš™ï¸ Pydantic Settings
â”‚   â””â”€â”€ main.py           # ðŸš€ App entry point
â”œâ”€â”€ tests/                # ðŸ§ª pytest suite
â”‚   â”œâ”€â”€ test_agents/      #    Agent/graph tests
â”‚   â””â”€â”€ test_api/         #    API endpoint tests
â”œâ”€â”€ scripts/              # ðŸ”Œ AI Logging Hooks
â”‚   â”œâ”€â”€ log_hook.py       #    Auto-log cho Claude/Cursor/Codex/Gemini/Copilot
â”‚   â”œâ”€â”€ log_antigravity.py#    Antigravity IDE prompt scanner
â”‚   â”œâ”€â”€ log_manual.py     #    Manual log cho ChatGPT / web tools
â”‚   â”œâ”€â”€ submit_log.py     #    Submit logs on git push
â”‚   â””â”€â”€ setup_hooks.sh    #    One-time hook installer
â”œâ”€â”€ .claude/ .codex/ .cursor/ .gemini/  # Per-tool hook configs
â”œâ”€â”€ .agents/              # Antigravity rules + workflows
â”œâ”€â”€ .ai-log/              # ðŸ“Š AI usage logs (auto-generated)
â”œâ”€â”€ docs/
â”‚   â”œâ”€â”€ guide/            # ðŸ“– Technical Guidebook (10 chapters)
â”‚   â””â”€â”€ architecture_diagram.md
â”œâ”€â”€ eval/                 # ðŸ“Š Evaluation results
â”œâ”€â”€ presentation/         # ðŸŽ¤ Demo Day slides
â”œâ”€â”€ .github/workflows/    # âš¡ CI/CD (GitHub Actions)
â”œâ”€â”€ .github/hooks/        # ðŸª Copilot hook config
â”œâ”€â”€ Dockerfile            # ðŸ³ Multi-stage build
â”œâ”€â”€ docker-compose.yml    # ðŸ™ Full stack orchestration
â””â”€â”€ README_boilerplate.md # ðŸ“ README template cho Ä‘á»™i cá»§a báº¡n
```

## ðŸ“š Technical Guidebook â€” 10 ChÆ°Æ¡ng

| ChÆ°Æ¡ng | Ná»™i dung | Thá»i gian |
|---------|----------|-----------|
| 1 | Lá»i má»Ÿ Ä‘áº§u â€” Má»¥c tiÃªu, cÃ¡ch sá»­ dá»¥ng | 15 phÃºt |
| 2 | Khá»Ÿi táº¡o dá»± Ã¡n â€” Clone, setup, git workflow | 4 giá» |
| 3 | Thiáº¿t káº¿ kiáº¿n trÃºc â€” 3-tier, diagrams, ADR | 6 giá» |
| 4 | **LangGraph Agent** â€” State, nodes, edges, tools, RAG | 8 giá» |
| 5 | FastAPI â€” Routes, validation, error handling, streaming | 6 giá» |
| 6 | Giao diá»‡n â€” Next.js + Streamlit quickstart | 6 giá» |
| 7 | DevOps â€” Docker, CI/CD, deploy, logging | 6 giá» |
| 8 | Kiá»ƒm thá»­ â€” Unit test, integration test, RAGAS | 4 giá» |
| 9 | Demo Day â€” 10 deliverables, checklist, tips | 2 giá» |
| 10 | TÃ i nguyÃªn â€” KhÃ³a há»c, docs, BMAD method | tham kháº£o |

ðŸ“– **Äá»c online:** [phoenix.note.transformerlabs.ai/technical-book](https://phoenix.note.transformerlabs.ai/technical-book)

## ðŸ“‹ 10 Deliverables cho Demo Day

| # | Deliverable | File vá»‹ trÃ­ | Template cÃ³ sáºµn |
|---|-------------|-------------|:---:|
| 1 | Source Code | `src/` | âœ… |
| 2 | README.md | `README_boilerplate.md` â†’ copy thÃ nh `README.md` | âœ… |
| 3 | Architecture Diagram | `docs/architecture_diagram.md` | âœ… |
| 4 | AI Logs | LangSmith (3 env vars) + Auto AI Usage Logging | âœ… |
| 5 | Live URL | Deploy lÃªn Render/Vercel | âš¡ CI/CD sáºµn |
| 6 | Video Demo | `presentation/` | ðŸ“ |
| 7 | Pitch Deck | `presentation/` | ðŸ“ |
| 8 | Development Journal | `JOURNAL.md` | âœ… |
| 9 | Worklog | `WORKLOG.md` | âœ… |
| 10 | Evaluation Evidence | `eval/` | ðŸ“ |

## ðŸ›  Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| AI Agent | LangGraph + LangChain | Latest |
| Backend | FastAPI + Uvicorn | 0.100+ |
| LLM | OpenAI GPT-4o-mini | API |
| Frontend | Next.js / Streamlit | 14+ / 1.30+ |
| Database | SQLite (dev) / PostgreSQL (prod) | â€” |
| DevOps | Docker + GitHub Actions | â€” |
| Testing | pytest + pytest-asyncio | 8+ |

## ðŸ“Š AI Usage Logging

Template Ä‘Ã£ tÃ­ch há»£p sáºµn auto-logging hooks cho 6 AI tools:

| Tool | CÆ¡ cháº¿ | Config |
|------|--------|--------|
| Claude Code | `.claude/settings.json` hooks | Tá»± Ä‘á»™ng |
| Cursor | `.cursor/hooks.json` | Tá»± Ä‘á»™ng |
| OpenAI Codex CLI | `.codex/hooks.json` | Tá»± Ä‘á»™ng |
| Gemini CLI | `.gemini/settings.json` | Tá»± Ä‘á»™ng |
| GitHub Copilot | `.github/hooks/hooks.json` | Tá»± Ä‘á»™ng |
| Antigravity IDE | Pre-push scan transcript | Tá»± Ä‘á»™ng trÃªn `git push` |

Táº¥t cáº£ prompts vÃ  tool calls Ä‘Æ°á»£c log vÃ o `.ai-log/session.jsonl` vÃ  tá»± Ä‘á»™ng submit lÃªn grading server má»—i khi `git push`.

**ChatGPT / web tools khÃ¡c** â€” log thá»§ cÃ´ng:
```bash
bash scripts/_pyrun.sh scripts/log_manual.py --tool chatgpt --prompt "What you asked"
```

> âš ï¸ Cháº¡y `bash scripts/setup_hooks.sh` má»™t láº§n sau khi clone Ä‘á»ƒ cÃ i pre-push hook.

## ðŸ“– Äá»c Technical Guidebook

**Online (khuyáº¿n nghá»‹):** [phoenix.note.transformerlabs.ai/technical-book](https://phoenix.note.transformerlabs.ai/technical-book)

ÄÄƒng nháº­p báº±ng GitHub (cÃ¹ng account Ä‘Ã£ Ä‘Æ°á»£c BTC má»i vÃ o org `AI20K-Build-Cohort-2`)
â†’ chá»n tab **Technical Book** á»Ÿ sidebar trÃ¡i â†’ Ä‘á»c 10 chÆ°Æ¡ng + topic sections,
cÃ³ table of contents bÃªn pháº£i, há»— trá»£ light/dark/cyberpunk theme.

**Offline:** má»i chÆ°Æ¡ng Ä‘á»u á»Ÿ thÆ° má»¥c `docs/guide/` trong template nÃ y â€” má»Ÿ báº±ng
báº¥t ká»³ markdown viewer/editor nÃ o (VS Code, Obsidian, GitHub UI, â€¦).

## ðŸ”— LiÃªn káº¿t

- ðŸ“– **Technical Guidebook:** [phoenix.note.transformerlabs.ai/technical-book](https://phoenix.note.transformerlabs.ai/technical-book)
- ðŸ« **AI20K Program:** VinUni AI20K Build Phase
- ðŸ‘¨â€ðŸ« **Mentor:** Äáº·ng Háº£i Lá»™c

## ðŸ“„ License

MIT â€” Sá»­ dá»¥ng tá»± do cho má»¥c Ä‘Ã­ch giÃ¡o dá»¥c.
