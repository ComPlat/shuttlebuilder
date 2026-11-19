#!/usr/bin/env bash
# Six-architecture smoke build of a ShuttleBuilder Docker image.
set -euo pipefail

usage() {
    cat <<'USAGE'
Usage: dev/smoke_build.sh [-h] <image> [shuttle-src] [branch]

Runs `manage.py shuttle_smoke_build` in <image> with a throw-away SQLite database.

  image        Docker image of ShuttleBuilder (e.g. shuttlebuilder:latest)
  shuttle-src  Git URL or local directory of the Shuttle source
               (default: https://github.com/ComPlat/shuttle.git); a local
               directory is mounted read-only at /shuttle
  branch       Branch or commit (default: main)

Exit code: the one of the smoke command (0 = all cases OK).
USAGE
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi
if [ "$#" -lt 1 ] || [ "$#" -gt 3 ]; then
    usage >&2
    exit 2
fi

image="$1"
src="${2:-https://github.com/ComPlat/shuttle.git}"
branch="${3:-main}"

mount_args=()
if [ -d "${src}" ]; then
    mount_args=(-v "$(cd "${src}" && pwd):/shuttle:ro")
    src="/shuttle"
fi

inner='git config --global --add safe.directory "*" \
    && rm -f test_db.sqlite3 \
    && python manage.py migrate -v0 \
    && python manage.py shuttle_smoke_build --shuttle-src "$1" --branch "$2"'

exec docker run --rm --entrypoint sh \
    -e DJANGO_DATABASE=jest -e MODE=develop \
    "${mount_args[@]+"${mount_args[@]}"}" \
    "${image}" -c "${inner}" sh "${src}" "${branch}"
