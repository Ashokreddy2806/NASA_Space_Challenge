# Instructions for AI Assistants

This repo is a 3-person, ~24-hour NASA Space Apps hackathon project. Every team member works with an AI assistant (Claude Code, Cursor, Copilot, ChatGPT, …). These rules keep everyone — humans and AIs — in sync. **Follow them on every task.**

## 1. Read first (every new session)

1. [PROBLEM_STATEMENT.md](PROBLEM_STATEMENT.md) — what we are solving. Don't change it unless asked.
2. [PLAN.md](PLAN.md) — approach, architecture, workstreams, decisions, open questions.
3. [PROGRESS_LOG.md](PROGRESS_LOG.md) — what each teammate has done and is doing now.

Before starting work, check the Workstreams table and the teammates' **Now working on** lines so you don't duplicate or overwrite someone else's work.

## 2. Know who you are working for

Team members: **rahul**, **ashok**, **mrinalini**.

Identify the current person from `git config user.name`:
- `rahuloruganti` → **rahul**
- anything else → **ask the person which teammate they are** before writing to the log. Don't guess.

## 3. Update the docs as you work (required)

After every meaningful change (new file, feature working, bug fixed, dataset downloaded, decision made), and before the person ends the session:

- **PROGRESS_LOG.md** — add an entry in **that person's section only**, newest at the top under `<!-- entries -->`, using the format at the top of the file. Update their **Now working on** line. Never edit or delete another member's entries.
- **PLAN.md**:
  - Workstreams table: set `Owner` when someone claims a workstream; update `Status`.
  - Timeline: tick `[x]` when a milestone is reached.
  - Decisions log: append any decision (dataset chosen, library chosen, target site chosen) as `YYYY-MM-DD HH:MM — name — decision — why`.
  - Open questions: tick when answered (and add the answer to the Decisions log); add new ones.
  - Results so far: add candidate sites as they are found.
  - Update the **Last updated** line.

Use real timestamps (`date "+%Y-%m-%d %H:%M"`). Keep entries short and concrete: file paths, numbers, dataset names.

## 4. Don't do these without the person's OK

- Don't assign workstreams to people. Only the team assigns work.
- Don't change PROBLEM_STATEMENT.md or reverse a recorded decision.
- Don't rewrite or reorganize other people's code or log entries.
- Don't commit large data files (raw/processed rasters, NetCDF, Zarr, GeoTIFF, HDF). They go in `data/` and stay git-ignored.

## 5. Git workflow

- `git pull --rebase` before starting and before pushing; the log and plan are edited by everyone.
- Commit small and often. Message format: `<area>: <what>` (e.g. `pipeline: regrid MODIS LST to 0.05deg`).
- **No AI attribution** in commit messages or PR descriptions: no `Co-Authored-By: Claude …` (or any other AI) trailer, no "Generated with …" lines. The commit author is the teammate.
- On a merge conflict in PROGRESS_LOG.md or PLAN.md: **keep both sides**, never drop a teammate's lines.

## 6. Technical guardrails

- Python backend. Reusable code lives in `backend/`; notebooks are for exploration only.
- Machines have ~8 GB RAM: use coarse global grids (~0.05°, ≈5 km) for the global search; fetch high-res data only for a few top candidate sites. Use lazy loading (xarray + dask/chunks) and avoid loading whole global rasters at full resolution.
- Every dataset used must be recorded in PLAN.md (product name, resolution, source URL).
- Visual quality matters a lot for judging — treat the frontend as a first-class deliverable.
- When reporting site similarity, always include what does **not** match and what Earth cannot replicate (gravity, vacuum / thin atmosphere, radiation).
