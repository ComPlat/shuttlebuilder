---
name: milestone-development
description: ShuttleBuilder development workflow. The Opus orchestrator works through dev/milestones.md one milestone at a time, with at most two Sonnet worker agents in the ../wt-a/ShuttleBuilder and ../wt-b/ShuttleBuilder worktrees. It reviews, merges, gates on Django checks, migrations, tests and a Shuttle build for all six architectures, and reports. Use it for every ShuttleBuilder milestone, work package, worker round, review/merge or milestone report; in this repo use it instead of two-worker-milestones.
---

# ShuttleBuilder milestone development

You are the **orchestrator** (Opus): you design, brief, review, fix problems that appear when worker changes are merged together, commit, merge and report. Up to two **Sonnet worker agents** write the code. The owner of the repo makes all product, release and security decisions.

## Owner rules (binding)

- **One milestone at a time.** Branch `milestone/mN-<slug>` from the latest `master`, and merge it back through a GitHub PR on `ComPlat/shuttlebuilder`. Stop after each milestone and report; start the next one only when the owner explicitly says so.
- **Clean checkout first.** The main checkout must be clean before a milestone starts. If it has uncommitted changes, ask the owner what to do with them; never stash or discard them yourself.
- **Never more than 2 workers at once.** Workers are Sonnet agents: Agent tool with `model: "sonnet"`, `subagent_type: "general-purpose"`, `run_in_background: true`. Workers never commit.
- **No broken merges.** Never merge code that fails the gate (§ A worker round, step 8) or its acceptance criteria. Make no unrelated changes, and stop when you hit a blocker.
- **Releases belong to the owner.** A new Docker image (`mstarman/shuttlebuilder:<version>`, `deploy.sh`) is what reaches the labs. Never run `deploy.sh`, `docker push` or bump the image tag in `docker-compose*.yml` unless the owner asks. Merge the PR only after the owner's OK.
- **Push only the milestone branch**, never `wt/*`.
- **Attribution:** commit trailer and PR footer follow the current system attribution rules.
- **Report after each milestone:** name, work packages done, verification (commands and results, including the build of each architecture), review findings and fixes, migrations, branch/merge status, risks, and what the Shuttle repo needs (cross-repo follow-ups).

## Roadmap: `dev/milestones.md`

- Take the first milestone without a status, or one marked `planned`, unless the owner names a different one. If the milestone is missing or vague, draft its goal, work packages and acceptance criteria with the owner first.
- On the milestone branch, add `**Status:** in progress` under the milestone heading; at the end, set it to `done (#PR)`. Tick the work-package checkboxes as they are finished.
- The "Global constraints" and "Definition of Done" sections at the top of the file apply to every work package. The "Owner decisions needed" list names the open choices: get those answers before the round that needs them, and record them in `dev/milestones.md`.

## What ShuttleBuilder does (the part that must not break)

`ShuttleInstance.build()` in `main_app/models.py` takes the checkout of the active `GitInstance` (`./projects/git_repos/<name>/`, a clone of `ComPlat/shuttle`), copies it to `./projects/builds/<instance>/src`, renders the files with Django `Template` and `_get_build_config()`, then runs `go build`. The result is downloaded through `main_app/sdc_views.py` (`ShuttleDownload`), packed with WinSCP or the converter where needed (`only_exe`); the start files come from `file_handler/views.py`.

| Architecture | GOOS/GOARCH | Toolchain |
|---|---|---|
| `ubuntu_64` | linux/amd64 | Go from `settings.GOROOT` (`Dockerfile`), modules |
| `raspberry_pi_6` / `_7` | linux/arm, `GOARM=6` / `7` | same |
| `raspberry_pi_64` | linux/arm64 | same |
| `win_64` (Windows 10/11) | windows/amd64 | same |
| `win_i386` (Windows XP) | windows/386 | `go1.10` wrapper in GOPATH mode, gowebdav via `go1.10 get` |

Rules that come from this:

- **The placeholder contract with Shuttle.** The keys of `_get_build_config()` must match the placeholders in Shuttle's `cmd_manager.go` (listed under "Contract with the Shuttle repo" in `dev/milestones.md`). An unknown key renders empty. Adding or renaming one is a cross-repo change: check `../Shuttle/cmd_manager.go` read-only, and list it in the report.
- **Every value ends up inside a Go string literal.** Until M1 WP 1.1 is done, rendering HTML-escapes values; after it, every string goes through the Go-literal escape helper. Never add a placeholder value that bypasses it.
- **Secrets live in the rendered sources and build folder.** Passwords, API keys and `cam_` tokens are compiled in. Never log rendered sources, `_get_build_config()` output or compiler output without redaction.
- **Model changes need a migration** in `main_app/migrations/`; `makemigrations --check` must be clean at the gate.
- **Model docstrings feed the AI assistant** (`SDC_SKILL.md`, see M6 WP 6.4). Keep them precise when fields change.

## Secrets and isolation

- **Never print secrets:** `.env`, `.env.dev`, the database password in `ShuttleBuilder/base_settings.py`, AI API keys, instance passwords and tokens, or GitHub tokens. The repo is public.
- **Workers get no `.env`.** They run everything with `DJANGO_DATABASE=jest` (SQLite, `test_db.sqlite3` in their own worktree) and `MODE` unset.
- **Tests never touch the real data:** no real Postgres, no `./projects/` of the main checkout, no network, no real `git clone`. Tests that exercise `build()`, `git_reload()` or downloads run inside a temporary working directory (`override_settings` plus `os.chdir` to a `tempfile.TemporaryDirectory`, or patch `get_path`) and mock `subprocess`, unless the test is the orchestrator's build smoke test.
- **Workers stay local.** They:
  - run no `docker compose up`, `deploy.sh`, `docker build` or `docker push`;
  - don't touch `../Shuttle` or its worktrees `../wt-a/Shuttle` and `../wt-b/Shuttle` (except reading `../Shuttle` when the brief says so);
  - don't call the AI provider or the ELN;
  - don't push.

## Environment

- **Repo:** `/home/martin/Deveolop/KIT/ShuttleContainer/ShuttleBuilder` (GitHub `ComPlat/shuttlebuilder`, main branch `master`). Django 6 on the `simpledomcontrol` (SDC) framework; apps `main_app` and `file_handler`. There is no `CLAUDE.md` yet. Read `README.md`, `dev/milestones.md`, `SDC_SKILL.md` and the touched source files before designing.
- **Sibling repo:** `../Shuttle` is the Go program that gets built, with its own `milestone-development` skill and milestones. Its worktrees already occupy `../wt-a/Shuttle` and `../wt-b/Shuttle`.
- **Worktrees:** `../wt-a/ShuttleBuilder` (branch `wt/mN-a`) and `../wt-b/ShuttleBuilder` (`wt/mN-b`):
  ```
  git worktree add ../wt-a/ShuttleBuilder -b wt/mN-a milestone/mN-<slug>
  ln -s /home/martin/Deveolop/KIT/ShuttleContainer/ShuttleBuilder/node_modules ../wt-a/ShuttleBuilder/node_modules
  ```
  Before each round, sync with `git -C ../wt-a/ShuttleBuilder merge --ff-only milestone/mN-<slug>`.
- **Python:** use the main checkout's Poetry venv in every worktree, by absolute path, so no second venv is created:
  `PY=/home/martin/.cache/pypoetry/virtualenvs/shuttlebuilder-Z_zR7Z5O-py3.14/bin/python` (check with `poetry env info -p` if it moved).
- **Django commands** (from the worktree root):
  ```
  DJANGO_DATABASE=jest $PY manage.py check
  DJANGO_DATABASE=jest $PY manage.py makemigrations --check --dry-run
  DJANGO_DATABASE=jest $PY manage.py test main_app file_handler
  ```
- **Frontend:** `Assets/` (SDC controllers, gulp). After changes to `main_app/Assets/` or templates used by controllers: `$PY manage.py sdc_update_links`, then `npm run build`; JS tests with `npm run sdc_test`.
- **Go toolchains for the smoke build:** `go` 1.26 on `PATH`; Docker images `golang:1.24.13` (the version in the `Dockerfile` today) and `golang:1.10.8` (XP). `go1.10` is not installed locally.
- **Design docs and round reports** go in `dev/mN/`, which is git-ignored by `/dev/m*/` in `.gitignore`. `dev/milestones.md` itself is tracked.

## A worker round

1. **Design first.** For non-trivial work packages (for example WP 1.1, WP 3.2 or M7), write `dev/mN/design.md`: numbered sections, a §0 "orchestrator amendments" that overrides the rest, and acceptance criteria. Get the owner's decision on open choices first.
2. **Split into disjoint scopes with explicit file ownership.** Seams that split well:
   - build pipeline: `ShuttleInstance._get_build_config`, `build`, `only_exe` (move new helpers into a new module such as `main_app/build.py` rather than growing `models.py`);
   - model fields and validation: the other parts of `main_app/models.py`, `main_app/forms.py`, the migration;
   - downloads and packaging: `main_app/sdc_views.py`, `file_handler/views.py`;
   - toolchain: `Dockerfile`;
   - UI and docs: `main_app/templates/`, `main_app/Assets/`, `README.md`, `SDC_SKILL.md`.

   `main_app/models.py` is the hotspot: if both workers need it in one round, give each one a clearly separated set of methods or classes, and say so in both briefs. Only one worker per round creates a migration. Split tests by owner: once a round needs tests from both workers, turn `main_app/tests.py` into a `main_app/tests/` package (`test_build.py`, `test_forms.py`, `test_packaging.py`, …) yourself before the round.
3. **Shared files belong to the orchestrator.** Workers list the edits they need in their report, and you apply them:
   - `pyproject.toml` / `poetry.lock`, `package.json` / `yarn.lock`;
   - `ShuttleBuilder/settings.py`, `ShuttleBuilder/base_settings.py`;
   - `docker-compose*.yml`, `deploy.sh`, `.env.sample`;
   - `.gitignore`, CI files;
   - `dev/milestones.md`;
   - migration numbering (renumber at merge if needed).
4. **The brief is the worker's entire context.** Include:
   - the absolute worktree path, with "work only there, never touch the main checkout, `../Shuttle` or `../wt-*/Shuttle`";
   - "read README.md, SDC_SKILL.md and dev/milestones.md (Global constraints, Definition of Done)";
   - the binding design sections, by path;
   - the exact work packages and scope;
   - file ownership, and what the other worker is doing;
   - "do not commit";
   - the secrets and isolation rules above, copied in;
   - the `$PY` path and the commands to run: `check`, `makemigrations --check` (or the one allowed `makemigrations main_app --name <slug>`), targeted `manage.py test main_app.tests.<module>`;
   - house style: Django forms do validation in `clean()`/validators, user-facing strings go through `gettext`, `subprocess.run` with argument lists, timeouts and captured output, no secrets in logs or exceptions;
   - the report file `dev/mN/round<k>-<topic>.md`: files, commands, results, deviations, needed shared-file edits;
   - context updates from earlier rounds.
5. **Launch both workers in one message.** You are notified when they finish. Never write watcher loops.
6. **Review each diff yourself** against the design and `dev/milestones.md`:
   - every changed existing test is a behaviour change you must justify;
   - placeholder keys still match Shuttle's `cmd_manager.go`, and every value goes through the escape helper;
   - no secrets in logs, messages, exceptions or test output; no rendered sources written outside the build folder;
   - migrations: one per model change, reversible data migrations, no hand-edited old migrations;
   - permission checks (`is_authorised`, `get_queryset`) not weakened; staff-only options stay staff-only;
   - help texts, README and `basic_info.html` updated when user-visible behaviour changed (Definition of Done).
7. **Commit and merge.**
   - Commit in each worktree with explicit `git add <files>`: `mN round k: <summary>`.
   - Merge into the milestone branch with `git merge --no-ff wt/mN-b`, then `wt/mN-a`.
   - Resolve conflicts; renumber clashing migrations and fix their `dependencies`. Workarounds a worker added outside its own files go back into the module that owns them.
   - Shared-file updates go in a separate commit.
8. **Run the gate serially** on the milestone branch in the main checkout:
   - `DJANGO_DATABASE=jest $PY manage.py check` and `makemigrations --check --dry-run` are clean;
   - `DJANGO_DATABASE=jest $PY manage.py test main_app file_handler` passes;
   - `npm run build` (and `npm run sdc_test`) when `Assets/` or controller templates changed;
   - **the six-architecture build** whenever the build pipeline, `Dockerfile`, packaging or placeholders changed (Definition of Done): until M5 WP 5.2 automates it, `docker build -t shuttlebuilder:mN .`, then inside that image create one test instance per architecture (plus one `win_i386` SFTP and WebDAV, plus one per new transfer type) against the active Shuttle checkout, call `build()`, and check each binary with `file`. Save the script in `dev/mN/` and the result in the report. Use dummy credentials only;
   - an end-to-end upload with a built Shuttle only when you choose to run it yourself, against a local test server, never from a worker.

   Fix bugs that come from two workers' changes interacting with one shared helper plus a regression test, in a separate commit.

## Finish

1. Push `milestone/mN-<slug>`.
2. Open the PR. Include: behaviour changes, work packages done, migrations, verification commands and results (including each architecture), and Shuttle cross-repo notes.
3. Get the owner's OK, then merge.
4. Mark the milestone `done (#PR)`.
5. Remove the worktrees (`git worktree remove ../wt-a/ShuttleBuilder`, same for `wt-b`) and delete the `wt/*` branches. Leave the Shuttle worktrees alone.
6. Report and stop. Mention whether a new Docker image is needed; building and deploying it is the owner's call.

## Pitfalls

- **zsh quirks:** zsh doesn't word-split unquoted variables, and `======` at the start of a line is a zsh `=command` expansion.
- **No `pgrep` watchers:** `pgrep -f "<pattern>"` in a loop matches its own shell. Background processes must be tracked tasks, not started with `&`.
- **Lots of untracked local data:** `db.sqlite3`, `test_db.sqlite3`, `media/`, `projects/`, `www/`, `static/` and the generated `Assets/` links are ignored but present. Never `git add -A`; commit with explicit `git add <files>`.
- **Relative build paths:** `get_path()` uses `./projects/...` relative to the current directory. A test or script run from the wrong folder writes into the main checkout's `projects/`.
- **`MODE` decides the database:** without `DJANGO_DATABASE=jest`, a dev run tries the local Postgres on port 65432 with the credentials in `base_settings.py`.
- **Two repos, same worktree folders:** `../wt-a/` holds both `Shuttle` and `ShuttleBuilder`. Double-check paths in every brief and `git -C` command.
- **Keep decisions durable:** scratchpad files vanish on reboot, so keep decisions in `dev/` or `dev/milestones.md`.
- **Blocked workers:** if a worker is blocked (quota, tooling), ask the owner whether to finish the round yourself, and report it as an exception.
