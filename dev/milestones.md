# ShuttleBuilder – Milestones for Shuttle 1.13 and fixes

Source: review of ShuttleBuilder `master` @ `6ec5ce3` (2026-11-18), after Shuttle 1.13 was merged (ComPlat/shuttle PRs #5–#11).
Goal: ShuttleBuilder builds correct Shuttle 1.13 binaries for every architecture, exposes the new Shuttle options, and its documentation matches what Shuttle and the install files actually do.

---

## Global constraints

### What ShuttleBuilder must keep doing

| Architecture | GOOS/GOARCH | Toolchain today | Ships |
|---|---|---|---|
| `ubuntu_64` | linux/amd64 | Go 1.24.13 (`Dockerfile`) | `shuttle` (+ converter zip) |
| `raspberry_pi_6` / `_7` | linux/arm, GOARM 6/7 | same | `shuttle` |
| `raspberry_pi_64` | linux/arm64 | same | `shuttle` |
| `win_64` | windows/amd64 | same | `shuttle.exe` (+ converter zip) |
| `win_i386` (Windows XP) | windows/386 | `go1.10` wrapper, GOPATH mode | `shuttle.exe`, or a zip with WinSCP for SFTP |

### Contract with the Shuttle repo
- `ShuttleInstance.build()` copies the active `GitInstance` checkout, renders files through Django `Template` with `_get_build_config()`, then runs `go build`.
- Shuttle's placeholders live in `cmd_manager.go`: `src dst user password duration common_regex tType name crt type preconvert dst_converter user_converter password_converter public` and, **new in 1.13**, `hostkey` and `insecure`. An unknown placeholder renders empty, which Shuttle treats as "not set".
- Shuttle's CI (`dev/check_templates.py`) already checks that every Shuttle file survives the template pass.

### Definition of Done (every WP)
- [ ] A build succeeds for all six architectures (WP 5.2 adds an automated smoke build; until then, build them by hand)
- [ ] New or changed behaviour has a test in `main_app/tests.py`, which is empty today
- [ ] Model changes come with a migration
- [ ] Help texts, the README and `basic_info.html` are updated in the same PR when user-visible behaviour changes (see M6)
- [ ] No secrets in logs or error pages

---

## M1 – Correct builds (bugs that affect every lab today)

**Status:** done (#2)

### WP 1.1 – Build values are HTML-escaped into the binary
- **Bug (verified):** `build()` renders with `django.template.Template`, where **autoescape is on** (default `TEMPLATES` in `base_settings.py`). A password `a&b<c>` is compiled in as `a&amp;b&lt;c&gt;`, and `it's` becomes `it&#x27;s`. The same happens to `src` paths (`C:\Data & Results`), URLs with `&`, and regexes with `<`/`>`. Those labs fail to log in or watch a folder that doesn't exist.
- **Files:** `main_app/models.py` (`_get_build_config`, `build`)
- **Tasks:**
  - [x] Render with autoescape off: `Context(..., autoescape=False)`, or an `Engine(autoescape=False)` used only for the build.
  - [x] Escape every value for a **Go string literal** instead of HTML: `\` → `\\`, `"` → `\"`, newline → `\n`, CR → `\r`, tab → `\t`. Do this in one helper, `go_str(value)`, applied to every string placeholder.
  - [x] Replace `replace_single_backslashes`. It leaves an already-doubled `\\` alone, which is why the UI tells users to type `\\`. **Owner decision needed:** stored values typed as `C:\\Data` must become `C:\Data` in a data migration (otherwise they would turn into a double backslash), or the old meaning stays for records created before the migration.
  - [x] Keep `replace_all_single_backslashes` semantics for `common_regex`. The regex goes into a Go string, so every backslash must be doubled, which `go_str` does anyway.
  - [x] Tests: render `cmd_manager.go`-style lines with values containing `& < > ' " \ newline`, and assert that the Go literal decodes back to the original value. Use a tiny `go run` or Python `ast`-style check of the escaping.
- **Acceptance:** a password `p&a<s>s'"\` works end to end, using a test instance against a local SFTP server.

### WP 1.2 – `crt` is hard-coded to `"None"`
- **Bug:** `_get_build_config` passes `"crt": "None"`. Shuttle 1.13 tries to read a file called `None` and logs a warning on every start. On Windows XP, a usable `-crt` is the only way to verify TLS.
- **Tasks:**
  - [x] Pass `""` until WP 3.2 provides real certificates.

### WP 1.3 – Only render what has placeholders
- **Risk:** every file of the Shuttle checkout goes through Django, including Markdown, YAML and Python. A single `{%` or a hyphenated `${{ a-b }}` anywhere breaks every build ("Compiling failed"). A binary file breaks it too, because files are opened in text mode with the default encoding.
- **Tasks:**
  - [x] Render only `*.go` files that aren't `_test.go`, and copy everything else unchanged. Coordinate with the Shuttle repo: its `dev/check_templates.py` and the skill rule can then be relaxed to `.go` files.
  - [x] Open files with `encoding="utf-8"`, and on failure name the file that failed.

### WP 1.4 – Build failures are invisible
- **Bug:** `go mod download` and `go build` output isn't captured. The user sees "There was en compilation error. Maybe you have used \ in the src instead of \\." That message is misleading, and wrong once WP 1.1 is done. Every other exception is swallowed with the same text.
- **Files:** `main_app/models.py` (`build`), `main_app/sdc_views.py` (`ShuttleDownload`)
- **Tasks:**
  - [x] Run `subprocess.run(..., capture_output=True, timeout=…)` and log stdout/stderr with the instance name, **without the rendered sources** (they contain passwords).
  - [x] Show staff a short error with the compiler's first lines (redacted); show users a neutral message plus a reference to the log.
  - [x] Fix the typo "en compilation error".

### WP 1.5 – Concurrent downloads of the same instance
- **Risk:** two simultaneous downloads (or a download while the `GitInstance` reloads) both `rmtree` and rebuild the same folder, and can serve a broken binary.
- **Tasks:**
  - [x] Lock per instance (a file lock in the build folder, or a DB `select_for_update`). Build into a temp folder and rename it into place.
  - [x] `git_reload` takes a global lock, so no build runs on a half-cloned repo.

---

## M2 – Toolchains and reproducible builds

**Status:** done (#3)

### WP 2.1 – Go 1.26 for modern builds
- **Why:** the `Dockerfile` installs Go **1.24.13**, which is out of upstream support. Standard-library vulnerabilities (crypto/tls, net/http, crypto/x509) end up in every lab binary. Shuttle had to keep x/crypto at v0.48.0, which still has 7 known vulnerabilities, because newer versions need Go ≥ 1.25.
- **Files:** `Dockerfile`
- **Tasks:**
  - [x] Install the latest Go 1.26.x patch release (pinned by version and SHA256 checksum).
  - [x] Set `ENV GOTOOLCHAIN=local`, so a future `go.mod` directive never triggers a silent toolchain download at build time.
  - [x] Build all six architectures with the current Shuttle `main` (go.mod `go 1.24`).
  - [ ] **Then** the Shuttle follow-up PR moves go.mod to `go 1.26` and updates x/crypto, x/sys and pkg/sftp to the latest versions (tracked in the Shuttle repo).
- **Acceptance:** `govulncheck` on a built Shuttle reports no reachable standard-library vulnerabilities.

### WP 2.2 – The XP toolchain is Go 1.10.0, not 1.10.8
- **Done differently (M2):** Go 1.10.8 is installed from its SHA256-pinned tarball at `/usr/local/go1.10.8` and selected by the setting `XP_GOROOT` (not a `go1.10.8` wrapper / `XP_GO_TOOL`); XP builds get `GOROOT=XP_GOROOT` explicitly.
- **Bug:** `go install golang.org/dl/go1.10@latest` installs the **Go 1.10.0** wrapper. Shuttle's CI (`dev/build_xp.sh`) verifies with **1.10.8**, the last 1.10 release, with its security fixes.
- **Tasks:**
  - [x] Use `golang.org/dl/go1.10.8` and `go1.10.8 download`, and call `go1.10.8` in `build()` (make it a setting, `XP_GO_TOOL`).
  - [x] Build a `win_i386` WebDAV and a `win_i386` SFTP instance.

### WP 2.3 – Pin `gowebdav` for the XP build
- **Risk:** `go1.10 get github.com/StarmanMartin/gowebdav` fetches the fork's **master** when the Docker image is built, so every image can contain different code. The modern builds use the version pinned in Shuttle's `go.mod` (`v0.0.0-20220901075112-8721ee532c0c`).
- **Tasks:**
  - [x] After `go get -d`, `git -C $GOPATH/src/github.com/StarmanMartin/gowebdav checkout 8721ee532c0c` (or read the pin from the active checkout's `go.mod` at build time).

### WP 2.4 – Build hygiene
- **Tasks:**
  - [x] Timeouts for `go mod download` and `go build`.
  - [x] Clean `tp_src` on failure as well; today it's only removed after success.
  - [x] `GOFLAGS=-buildvcs=false` (the checkout has no `.git`; this keeps future Go versions from failing on VCS stamping).

---

## M3 – Shuttle 1.13 options in the UI

**Status:** done (#4)

### WP 3.1 – SSH host key (`-hostkey`)
- **Shuttle behaviour:** `-hostkey` pins the server key, as `SHA256:…`, WinSCP style `ssh-ed25519 255 SHA256:…`, or MD5. Without it, Shuttle trusts the first key it sees (stored in `known_hosts`) and refuses a later change. On Windows XP, WinSCP needs either `-hostkey` or a key accepted once in the WinSCP GUI.
- **Files:** `main_app/models.py`, `main_app/forms.py`, a migration, `_get_build_config`
- **Tasks:**
  - [x] `host_key = CharField(blank=True)`, validated by regex for the three forms. Also add `host_key_bagit` for the converter destination, or document that both destinations need the same host.
  - [x] Pass it as `"hostkey"`.
  - [x] Help text: how to get the fingerprint (WinSCP *Session → Server/Protocol Information*; `ssh-keyscan -p <port> <host> | ssh-keygen -lf -`).
  - [x] **Strongly recommended for `win_i386` + SFTP:** show a hint, or make it required, because otherwise the XP Shuttle can't upload until someone accepts the key in WinSCP on the lab PC.

### WP 3.2 – Server certificate (`-crt`)
- **Shuttle behaviour:** WebDAV TLS is verified on modern builds. A self-signed server needs `-crt`. **Windows XP verifies only when `-crt` is given.**
- **Tasks:**
  - [x] `cert = FileField(upload_to="certs/", blank=True)`, PEM only (validate by parsing).
  - [x] When set, download a zip with the executable plus `server.crt`, and pass the **file name** as `crt`.
  - [x] **Cross-repo dependency:** Shuttle reads `-crt` relative to the *working directory*. The `.vbs`/systemd setups don't define it, so Shuttle must resolve a relative `-crt` against the executable's folder. This needs a small Shuttle PR first; until then, pass the absolute install path from M4.
  - [x] Packaging (`only_exe`, `sdc_views.ShuttleDownload`): add `server.crt` to every zip variant, and switch "exe only" to a zip when a cert is present.

### WP 3.3 – Disable verification (`-insecure`)
- **Tasks:**
  - [x] `insecure = BooleanField(default=False)`, passed as `"insecure": "1"` or `""`.
  - [x] **Owner decision:** visible to everyone, or only to staff.
  - [x] Show a clear warning in the form and in the instance list when it's on.

### WP 3.4 – Help texts and validation for 1.13 semantics
- **Tasks:**
  - [x] `dst`/`dst_bagit` help: SFTP accepts `host[:port]/path`, `ssh://…` and `sftp://…` (the port defaults to 22); WebDAV must start with `https://` (or `http://`). Validate this in the form, mirroring Shuttle's `parseDst`, so a bad value is caught before building.
  - [x] `duration` must be > 0; Shuttle 1.13 refuses 0. `PositiveIntegerField` allows 0, so add `MinValueValidator(1)`.
  - [x] `shuttle_type` help text: mention `flat_tar` (it's missing), and that a changed folder is sent again **completely**.
  - [x] `src` help: remove the "use `\\`" advice after WP 1.1.

### WP 3.5 – Show which Shuttle version is built
- **Why:** builds only pick up a new Shuttle after the active `GitInstance` is reloaded. Nobody can see which version a download contains.
- **Tasks:**
  - [x] After `git_reload`, read `const shuttleVersion = "…"` from `main.go` and store it on `GitInstance` (a migration).
  - [x] Show it in the git-instance list and on the download button. Record `built_version` on `ShuttleInstance` at build time.
  - [x] Roll-out note for admins: reload `ComPlat/shuttle/Main` to deliver 1.13.

---

## M4 – Packaging and install files

**Status:** done (#5)

### WP 4.1 – Install paths don't match the start files
- **Bug:**
  - The Windows start script (`file_handler/views.py`, `DownloadVbs`) runs `C:\Program Files\Shuttle\shuttle.exe`, but the README and `basic_info.html` say to create `C:\Program Files\eln_exporter` and copy the exe into `C:\Program Files\file_exporter`. Those two even differ from each other.
  - On Linux, `shuttle.service` starts `/opt/Shuttle/shuttle`, but the docs say `/opt/file_exporter`.
  - Labs that follow the docs end up with a Shuttle that never starts.
- **Tasks:**
  - [x] One path per OS. Proposal: `C:\Program Files\Shuttle` and `/opt/Shuttle`, matching the existing start files, so installed labs keep working.
  - [x] Fix the README, `basic_info.html` and the WinXP steps to match.

### WP 4.2 – systemd unit
- **Tasks:**
  - [x] `After=network-online.target` plus `Wants=network-online.target`. Shuttle 1.13 tolerates a missing network, but this avoids noise.
  - [x] `RestartSec=10`. Shuttle 1.13 exits on configuration errors (for example a missing converter or an unreadable scripts folder), and with `RestartSec=1` plus `StartLimitIntervalSec=0` it restarts every second forever.
  - [x] Replace `User=!!!!` with a generated file per instance, with the user taken from a form field, or at least a clear `User=CHANGE_ME` plus a comment.
  - [x] `Description=Shuttle (<instance name>)`; Shuttle stops cleanly on SIGTERM (the default `KillSignal`).

### WP 4.3 – Download view robustness
- **Tasks:**
  - [x] The `win_i386` branch assumes "SFTP without converter". It would silently drop the converter and profile if one were set. The form forbids that, but `build()`/the download should check `architecture`/`with_converter` again (admin and API can bypass the form).
  - [x] Build zips in a temp file instead of a fixed name in the build folder, so concurrent downloads don't clash (see WP 1.5).
  - [x] Optional: add a short `INSTALL.txt` to every zip (paths from WP 4.1, where logs and the sent register live).

---

## M5 – Tests and CI

**Status:** done (#7)

**Decided (2026-11-18):** GitHub Actions: checks and tests (Python + jest) on every PR and push; Docker image + six-architecture smoke build when the Dockerfile, build code, packaging or the smoke command change, and on manual trigger. `deploy.sh` runs the smoke build against the new image and aborts on failure.

### WP 5.1 – Unit tests (`main_app/tests.py` is empty)
- **Tasks:**
  - [x] `_get_build_config`/`go_str` escaping (WP 1.1).
  - [x] Form validation: converter only on `win_64`/`ubuntu_64`, `dst` formats, duration, host key formats, cert PEM.
  - [x] Packaging matrix (`only_exe`, the zip contents per architecture, transfer, converter and cert), with the build mocked.

### WP 5.2 – Build smoke test
- **Tasks:**
  - [x] A management command or CI job that builds one instance per architecture from the active `GitInstance` inside the Docker image, and checks that each binary exists, with `file` output matching the architecture.
  - [x] Run it in CI on every Dockerfile change, and before releasing a new image.

---

## M6 – Documentation

**Status:** in progress

**Decided (2026-11-19):** WP 6.5 delivers tracked drafts `docs/chemotion-data-transfer.md` and `docs/announcement-shuttle-1.14.md` (the owner submits/sends them). `SDC_SKILL.md` is regenerated by the orchestrator with `manage.py sdc_teach --fixture teacher --user teacher --password teach-me-2026 --no-ask` after the docstrings are updated.

Everything that users or admins read, aligned with Shuttle 1.13 and with M1–M5.

### WP 6.1 – README (repo)
- **Tasks:**
  - [ ] **Install steps** with the paths from WP 4.1, for Windows (`.vbs` in `shell:startup`), Windows XP (zip with WinSCP), and Linux (systemd from WP 4.2).
  - [ ] **What Shuttle 1.13 does after installation:**
    - working folder `~/shuttle/shuttle_<name>/` (Windows `%USERPROFILE%\shuttle\shuttle_<name>\`), with `shuttle_log.txt`, `sent_register.json` and `known_hosts`;
    - **the first start sends every stable file already in the source folder once**;
    - a changed folder is re-sent completely;
    - network outages are retried;
    - how to force a resend (delete `sent_register.json`).
  - [ ] **Security:** self-signed WebDAV servers need the certificate (M3); SFTP host key (pin vs trust on first use; what to do after a server key change); `-insecure`.
  - [ ] **Windows XP:** WinSCP must be next to `shuttle.exe`; host key; `-crt`; the open manual XP test (Shuttle issue).
  - [ ] **Admins:** Docker image toolchains (Go 1.26.x, Go 1.10.8 for XP), and how to roll out a new Shuttle version (reload the `GitInstance`, version display from WP 3.5).
  - [ ] Fix the typos ("Chomtion", "mirrow", "Networg").

### WP 6.2 – In-app docs (`main_app/templates/main_app/sdc/basic_info.html`)
- **Tasks:**
  - [ ] Mirror WP 6.1 (install paths, XP, Linux, first-start behaviour, log location).
  - [ ] Link to the troubleshooting section: where the log is, typical messages ("will retry", "host key CHANGED", "TLS certificate verification is DISABLED").

### WP 6.3 – Scripts page (`shuttle_scripts.html`)
- **Tasks:**
  - [ ] Rules from Shuttle 1.13:
    - Windows: only `.exe` (any case); `.bat`/`.cmd`/`.sh` are not run;
    - Linux: every executable regular file, including symlinks;
    - hidden files are never run;
    - scripts run in alphabetical order.
  - [ ] The converter: missing or failing → the conversion is skipped, the raw data is still sent. A missing converter with "With converter" checked → Shuttle stops at startup with a clear message.

### WP 6.4 – Form help texts and model docstrings
- **Tasks:**
  - [ ] All help texts touched in M3 (dst formats, host key, cert, insecure, duration, flat_tar).
  - [ ] Model docstrings (`GitInstance`, `ShuttleInstance`): new fields and version display. These docstrings feed the AI assistant (`SDC_SKILL.md`), so keep them precise.
  - [ ] `SDC_SKILL.md`: new fields, buttons and pages.

### WP 6.5 – External documentation and announcement
- **Tasks:**
  - [ ] Update the Chemotion docs page linked from the README and the app (`https://chemotion.net/docs/eln/devices/configurations/data_transfer`); that's a separate repository. Cover install paths, 1.13 behaviour, the security options and XP.
  - [ ] An announcement text for labs before rolling out 1.13:
    - re-upload on the first start;
    - self-signed WebDAV needs the certificate;
    - the SFTP host key is trusted on the first connection;
    - XP SFTP is untested on real hardware.

---

## M7 – New transfer type: ChemAssistentManager upload

**Depends on:** Shuttle milestone M8, which adds `-transfer chemassistent`. The Shuttle owner decisions there (type name, token flag, `-dst` form, folder mode, preconvert) fix the details below; the proposed options are assumed here.

**Goal:** a Shuttle instance can send its files to a ChemAssistentManager job (`POST <server>/api/jobs/trigger` with `Authorization: Bearer cam_…`). Each upload starts one run of that job's AI agent.

### WP 7.1 – Model, form and validation
- **Files:** `main_app/models.py` (`TRANSFER_CHOISES`, `ShuttleInstance`), `main_app/forms.py`, a migration
- **Tasks:**
  - [ ] Add `('chemassistent', _('ChemAssistent job (HTTP upload)'))` to `TRANSFER_CHOISES`.
  - [ ] **The API key:**
    - with Shuttle M8 decision 2, option A: reuse the `password` field. When `transfer == chemassistent`, the form labels it "API key (cam_…)" and hides or clears `user`, since it's not used;
    - with option B: a new `api_token` field, passed as the `token` placeholder.
    - Either way, validate the `cam_` prefix and a reasonable length.
  - [ ] `dst` validation for this type: `https://` (or `http://` for test setups) plus a host; a path is optional, because Shuttle appends `/api/jobs/trigger`. Reuse the M3 WP 3.4 validator.
  - [ ] Settings that don't apply to this type:
    - `host_key` is SSH only;
    - `cert`/`insecure` apply, as for WebDAV;
    - `with_converter` is rejected for this type, following Shuttle M8 decision 5.

    Hide the fields that don't apply in the form, and enforce the rules in `clean()`.
  - [ ] `shuttle_type` hint for this type: `folder` sends the whole folder as **one** run, `zip`/`tar` one archive per run, and `file`/`flat_tar` one run per file. File names are flattened (`A/B/x.csv` → `A__B__x.csv`).
  - [ ] Optional: a per-instance upload size limit (Shuttle `-maxUpload`, if Shuttle M8 adds it), defaulting to 100 MB to match the server's `JOB_MAX_UPLOAD_MB`.

### WP 7.2 – Build configuration and packaging
- **Files:** `main_app/models.py` (`_get_build_config`, `only_exe`), `main_app/sdc_views.py`
- **Tasks:**
  - [ ] Pass the type as `tType`, and the key as `password` (option A) or `token` (option B), escaped with the `go_str` helper from M1 WP 1.1. **An API key with `&` or `'` would otherwise be HTML-escaped**, the bug fixed in M1.
  - [ ] `only_exe`: no WinSCP for this type on `win_i386`, since it's plain HTTPS, so download only the exe (plus `server.crt` if set, from M3 WP 3.2).
  - [ ] XP note: Go 1.10 speaks at most TLS 1.2. The ChemAssistentManager server must offer TLS 1.2 for XP Shuttles; document this, and optionally warn in the form for `win_i386`.

### WP 7.3 – Linking to ChemAssistentManager (optional)
- **Tasks:**
  - [ ] A setting `CHEMASSISTENT_URL`: if set, the form pre-fills `dst` and shows a link "Create a job and an API key in ChemAssistentManager".
  - [ ] Not part of this milestone: creating the key automatically through an API, since ChemAssistentManager has no such endpoint today.

### WP 7.4 – Tests
- **Tasks:**
  - [ ] Form validation for the new type: `dst` forms, key format, rejected converter, ignored host key.
  - [ ] `_get_build_config` for the type, including escaping of the key.
  - [ ] Packaging: `win_i386` + `chemassistent` gives the exe only, without WinSCP.
  - [ ] Build smoke test (M5 WP 5.2): one `chemassistent` instance per architecture.

### WP 7.5 – Documentation
Part of M6, but listed here so it isn't forgotten.
- **Tasks:**
  - [ ] README and `basic_info.html`:
    - what the type does;
    - the steps: create a job with the "HTTP file upload" trigger in ChemAssistentManager, create an API key (shown once), create the Shuttle instance with the server URL and key;
    - one upload = one AI run;
    - the size limit and the TLS 1.2 note for XP;
    - a revoked key means files wait locally until the instance gets a new key and is rebuilt.
  - [ ] Form help texts and the `ShuttleInstance` docstring (feeds `SDC_SKILL.md`): the new type and how the password/token field is used for it.
  - [ ] The announcement (M6 WP 6.5): mention the new type.

---

## Suggested order and dependencies

```
M1 (1.1 → 1.2 → 1.3 → 1.4 → 1.5) ──► M2 ──► M3 ──► M4 ──► M5 ──► M6
                                    │                  ▲
                                    └─ Shuttle PR: go 1.26 + latest x/crypto (after WP 2.1)
M3 WP 3.2 ◄── Shuttle PR: resolve relative -crt against the executable's folder
M7 ◄── Shuttle M8 (new transfer type `chemassistent`); needs M1 WP 1.1 (escaping) first
```

- Do M1 first: WP 1.1 and WP 4.1 affect labs **today**, before 1.13 matters.
- Roll out Shuttle 1.13, that is reload the `GitInstance`, only after WP 1.2 (the `crt` warning) and the WP 6.5 announcement.
- M6 can start in parallel for the parts that don't depend on M3/M4: the 1.13 behaviour, XP and scripts.

## Owner decisions needed
1. **WP 1.1, existing records:** convert stored `\\` to `\` (a data migration), or keep the old meaning for old records?
   **Decided (2026-11-18): data migration.** Each stored value becomes what Shuttle actually received before (Go-decode of the old rendering); values that could never compile stay unchanged.
2. **WP 3.3:** may every user set `-insecure`, or only staff?
   **Decided (2026-11-18): every user**, with a clear warning in the form and the instance list.
3. **WP 3.1:** require a host key for `win_i386` + SFTP, or only recommend it?
   **Decided (2026-11-18): required** (unless `insecure` is set).
4. **WP 4.1:** keep `C:\Program Files\Shuttle` and `/opt/Shuttle` (matching the start files), or change the start files to a new path?
   **Decided (2026-11-18): keep `C:\Program Files\Shuttle` and `/opt/Shuttle`.** WP 4.2: the systemd unit is generated per instance with a new optional field `linux_user` (empty → `User=CHANGE_ME`). WP 4.3: every zip gets an `INSTALL.txt`.
5. **WP 1.3:** render only `*.go` files (recommended), or keep rendering every file?
   **Decided (2026-11-18): render only `*.go` files that are not `_test.go`;** copy everything else unchanged.

6. **M7:** inherits the decisions of Shuttle M8 (type name, token flag, `-dst` form, folder mode, preconvert).

## Cross-repo follow-ups (Shuttle)
- go.mod `go 1.26` and the latest x/crypto, x/sys and pkg/sftp, after WP 2.1.
- Resolve a relative `-crt` against the executable's folder (needed by WP 3.2).
  **Decided (2026-11-18): Shuttle fix first.** ShuttleBuilder passes `crt="server.crt"` and bundles the file; M3 is deployed only after the Shuttle fix is merged and the `GitInstance` reloaded.
- Once WP 1.3 is done: relax `dev/check_templates.py` to `.go` files.
- The open manual Windows XP test of Shuttle M5.
- Shuttle M8: the `chemassistent` transfer type, which ShuttleBuilder M7 needs.
