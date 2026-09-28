#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PYTHON="${DIR}/.venv/bin/python"
INSILOS_BIN="${DIR}/insilos-bin"
CONFIG="${DIR}/insilos.conf"

exec "${PYTHON}" "${INSILOS_BIN}" -c "${CONFIG}" "${@:---dev=xml}"
