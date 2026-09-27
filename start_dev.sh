#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
PYTHON="${DIR}/.venv/bin/python"
ODOO_BIN="${DIR}/odoo-bin"
CONFIG="${DIR}/odoo.conf"

echo "Starting Odoo 20.0 Dev Server..."
exec "${PYTHON}" "${ODOO_BIN}" -c "${CONFIG}" --dev=all "$@"
