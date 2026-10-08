# ProjectPilot — local workbench

Build useful software with small tasks, real file changes, visible costs, and your approval. This is an independent upgrade of the uploaded **Appbuilder--main.zip** project. The unrelated GitHub repository was not used.

## Start here

Install **Python 3.11+** and **Git**, unzip this package, open a terminal in the `ProjectPilot` folder, and run:

```sh
python run.py
```

On systems where Python is named `python3`, use `python3 run.py`. First launch creates a virtual environment and downloads the pinned Python dependencies. The frontend is already built and included. Open **http://127.0.0.1:8000**. Stop with Ctrl+C.

`python run.py --check` reports prerequisites without installing or starting anything. `python run.py --port 8001` uses another local port. Do not start multiple instances against the same data folder.

The app itself has no account, subscription, hosted database, or required model key. It runs on a computer, not directly inside an iPhone ZIP viewer. A secure hosted/mobile version is a future phase.

## First useful result — no integrated model spend

1. Create a project with your own brief. Each project gets a separate managed folder.
2. On Master Plan, generate a **free brief scaffold**, or copy the planning prompt into a coding tool you already use and import its JSON plan. The free scaffold groups your actual requirements; it is not an AI architecture review.
3. Read the plan and click **Adopt this version**. Generate delegation and add its tasks to the queue. You can also create a focused task manually.
4. Open an unblocked task. Copy its prompt into your existing coding tool. Paste the tool’s JSON result into the import panel, or open a JSON file. This creates actual candidate files and a real diff.
5. Run the available checks. Preview static HTML/CSS/JavaScript, inspect changes, and check each acceptance criterion yourself.
6. Click **Approve & commit locally**. Only this explicit action writes the approved changes into the managed Git repository. Export approved source from Overview.

For a quick smoke test, import `examples/first-task-result.json` into a manual task. It contains a small, real interactive counter page, clearly a sample—not generated output or a finished client project.

You can import an existing **source ZIP** from Overview. It creates a review task, never an automatic commit. Limits: UTF-8 text/SVG, 200 source files, 500 KB per file, 5 MB compressed / 20 MB expanded. Dependency folders are skipped; credentials and symlinks are rejected. Binary assets are not supported by this importer yet. Repository URLs and local paths entered in project metadata do not clone or modify those locations.

## Pay when the capability is worth it

There are three working paths:

| Path | Good use | What is measured |
|---|---|---|
| Copy prompt / import JSON | Reuse an existing ChatGPT, Gemini, Copilot, OpenCode or other workflow; manual edits | ProjectPilot makes no model call. External tool costs are unknown. |
| Local Ollama | Bounded tasks on hardware you already own | Reported tokens and duration; no API fee. Electricity/hardware cost is unknown. |
| Opt-in OpenRouter | Standard implementation or difficult reasoning when worth paying | Current catalog prices, per-request reservation, reported provider cost and tokens. |

### Optional paid setup

1. Copy `backend/.env.example` to `backend/.env` and set `OPENROUTER_API_KEY`. Restart the app. Do not put the key into source files or browser settings.
2. In Settings, enable paid requests, choose a monthly budget and per-run cap, load the current model catalog, and choose Standard and Advanced models.
3. In a task, choose a tier or leave Auto. Click **Choose route & estimate**, review the model and reservation, then **Run paid model** when you want to spend.

No named model is hardcoded as universally “best.” Auto is a transparent heuristic: use local for ordinary tasks when configured, otherwise Standard; suggest Advanced for complexity cues or two earlier attempts. It is not a benchmark or proof of quality. Explicit tiers override it. Every integrated attempt requires your action and counts against the task attempt cap. A failed check never starts another paid request automatically.

The estimator conservatively counts UTF-8 input bytes plus message overhead, caps output, and adds a 10% margin. It is a reservation, **not a guaranteed invoice maximum**. Current token-price ceilings and no provider fallbacks are sent with the request. A quote expires after five minutes and becomes invalid if the task context, settings or approved source change. Monthly allowance is shared across projects. Actual provider-reported usage replaces a reservation—even when the returned code/JSON is invalid. Unknown/failed/cancelled requests keep their reservation for that month. Check the provider dashboard for unresolved charges; configure a provider-side key credit limit as an additional control.

Prompts and selected source files leave your computer only when you choose an integrated cloud run or copy them into an external tool. No paid model requests were made to validate this delivery. Cloud request/response and failure handling are covered by local contract tests; real provider acceptance and model quality require a configured-key smoke test.

### Optional local setup

Install Ollama separately, download a model appropriate for your own hardware, start its server, and refresh local capabilities in Settings. Select an installed model. ProjectPilot does not download models and rejects cloud/remote entries from the local model list. Default endpoint: `http://127.0.0.1:11434`.

## What verification means

- Real source checks reject protected paths and symlinks. JSON and Python are parsed without running the source. Node checks JavaScript syntax without executing it. Install Node to enable JavaScript checks.
- These checks **do not prove runtime correctness, accessibility, security, or business accuracy**. You must exercise the acceptance criteria.
- TypeScript/JSX and framework projects require actual build commands. Missing checks are marked **blocked**, and block approval. Add commands by editing the failed/queued task’s contract or importing a plan with commands.
- Build commands never run on the host. The optional Docker runner uses an existing, explicitly configured image, disabled network, resource limits, read-only container root, no capabilities, and a temporary source copy. It does not install dependencies or pull images automatically. Docker remains an isolation boundary, not a formal security guarantee.
- To enable it, prepare a trusted image with your project’s runtime/check tools and offline dependencies, then set `PP_SANDBOX_IMAGE=your-image:tag` in `backend/.env` and restart. Commands run under `/workspace`. Internet-dependent `npm install` will fail by design. Prepare dependencies into the image yourself before running checks.
- The built-in preview serves **actual static source** in a sandboxed iframe. It blocks external APIs/forms and workspace access. It is not a React dev server, full backend deployment, or a mock render. Build/export framework apps separately. Docker builds currently retain check logs, not a hosted build artifact.

A verification record is tied to the exact candidate, approved baseline, and task contract. Changed or stale evidence cannot approve another version. If another task changed approved source, create a fresh task/candidate using the latest baseline. This release does not automatically rebase stale candidates.

## Keep ownership and recover

`data/projectpilot.sqlite3` stores project records. `data/projects/<project-id>/source` contains each managed Git repository. `candidates` contains isolated proposed snapshots; candidate names are workspace identifiers, **not actual Git branches**. Approved changes produce genuine local commits on `main`. Git remotes, remote merges, push, and deployment are intentionally not connected.

Overview exports approved source and lists commit history. **Review restore** turns an earlier commit into a new candidate; verification and your approval are still required. Projects are archived, not deleted. Restore an archive from its Overview.

Settings → **Download workspace backup** exports the database, candidates, and local Git history. To restore:

1. Stop ProjectPilot.
2. Keep a copy of the current `data` directory.
3. Unzip the backup into a separate folder and move its `data` directory into the ProjectPilot folder (or your configured `PP_DATA_DIR`).
4. Restart. Review interrupted tasks rather than retrying them blindly.

Backups contain your source, briefs, usage and review history. Provider/access keys are outside the data folder and must be backed up separately if desired. The original uploaded archive is unchanged. The old mock build’s historical documents live under `legacy` and are not current evidence.

## Develop this app

React remains JavaScript. FastAPI remains the backend. MongoDB was replaced with SQLite to remove a server/deployment dependency for this single-owner local edition. CRA was replaced with Vite and lazy-loaded routes; the existing design and navigation were retained. Existing MongoDB data is not automatically migrated; no database snapshot was included in the upload.

```sh
python -m venv .venv
# macOS/Linux:
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest
# Windows: use .venv\Scripts\python.exe instead.
```

For frontend changes, install a Node release supported by the pinned Vite version, then:

```sh
cd frontend
npm ci --legacy-peer-deps
npm run build
```

Restart the backend after rebuilding. For development, `npm run dev` serves port 5173 and proxies API/preview requests to port 8000.

The backend is loopback-only and designed for one owner and **one Uvicorn worker**. An optional `PP_ACCESS_TOKEN` adds a workspace API header check; this is not multi-user authentication. Do not expose the server publicly or mount arbitrary repositories into it. Public hosting needs real authentication, per-user authorization, distributed locks/queues and hardened isolated workers.

## The five highest-value improvements

1. **Real, reviewable delivery:** actual files, diff, check evidence, explicit approval, local Git checkpoints and restoration.
2. **Spend on the right task:** manual/local/standard/advanced routes, current estimates, shared budget, output and attempt caps, no automatic paid repair loop.
3. **Preserve project intent:** full task prompts and criteria, adopted plan versions, dependencies and changed-brief protection.
4. **Own and recover your work:** isolated projects, source ZIP import/export, SQLite, complete backups, archives instead of destructive reseeding.
5. **Keep context focused:** whole-file context selection, omitted-file disclosure, bounded requests and sequential generation.

Next priorities, only when needed: binary asset import and built-artifact previews; provider receipt reconciliation; task benchmarks to improve routing; remote Git authorization; secure hosted workers and multi-user access. These are future work, not claimed as delivered.

## Integration references

Implementation checked against [Ollama chat API](https://docs.ollama.com/api/chat), [OpenRouter model catalog](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties), [OpenRouter usage accounting](https://openrouter.ai/docs/cookbook/administration/usage-accounting), and [OpenRouter provider price limits](https://openrouter.ai/docs/guides/routing/provider-selection). Prices are fetched at runtime rather than copied into this document.
