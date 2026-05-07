#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${PYTHON_BIN:-"$ROOT_DIR/.venv/bin/python"}"
APP_NAME="${APP_NAME:-server-cli}"
DIST_DIR="${DIST_DIR:-"$ROOT_DIR/dist"}"
BUILD_DIR="${BUILD_DIR:-"$ROOT_DIR/build"}"
SPEC_DIR="${SPEC_DIR:-"$BUILD_DIR/spec"}"
ENTRYPOINT="$ROOT_DIR/main.py"

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Build main.py as a single executable with PyInstaller.

Options:
  --name NAME        Executable name. Default: server-cli
  --python PATH      Python interpreter. Default: .venv/bin/python
  --dist DIR         Output directory. Default: ./dist
  -h, --help         Show this help.

Environment variables:
  APP_NAME           Same as --name
  PYTHON_BIN         Same as --python
  DIST_DIR           Same as --dist

Examples:
  scripts/build_executable.sh
  scripts/build_executable.sh --name jsvc
  PYTHON_BIN=/usr/bin/python3 scripts/build_executable.sh
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name)
      APP_NAME="$2"
      shift 2
      ;;
    --python)
      PYTHON_BIN="$2"
      shift 2
      ;;
    --dist)
      DIST_DIR="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python interpreter not found or not executable: $PYTHON_BIN" >&2
  echo "Create the virtual environment first:" >&2
  echo "  python3 -m venv .venv" >&2
  echo "  .venv/bin/python -m pip install -r requirements.txt" >&2
  exit 1
fi

if ! "$PYTHON_BIN" -m PyInstaller --version >/dev/null 2>&1; then
  echo "PyInstaller is not available for: $PYTHON_BIN" >&2
  echo "Install dependencies first:" >&2
  echo "  $PYTHON_BIN -m pip install -r requirements.txt" >&2
  exit 1
fi

mkdir -p "$DIST_DIR" "$BUILD_DIR" "$SPEC_DIR"

"$PYTHON_BIN" -m PyInstaller \
  --onefile \
  --clean \
  --name "$APP_NAME" \
  --distpath "$DIST_DIR" \
  --workpath "$BUILD_DIR/pyinstaller" \
  --specpath "$SPEC_DIR" \
  "$ENTRYPOINT"

chmod +x "$DIST_DIR/$APP_NAME"

cat <<EOF

Build completed:
  $DIST_DIR/$APP_NAME

Try:
  "$DIST_DIR/$APP_NAME" --help

Note:
  Put config.json in the directory where you run the executable, or use commands
  that support --install-dir and --jar.
EOF
