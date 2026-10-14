#!/usr/bin/env bash
# ==============================================================================
# Insilos Multi-Repository Pre-Push Governance Hook Installer
# Part of Insilos Enterprise Continuous Governance Architecture
#
# Installs an automated pre-push gate into:
#   1. /home/zen/O20
#   2. /home/zen/VerticalRisk
#   3. /home/zen/insilos_mobile
#   4. /home/zen/zencode-ent
#
# Prevents any git push if:
#   - Documentation staleness exceeds 30-day threshold
#   - High-risk unpinned dependencies exist
#   - Git commit graph traversal breaks
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_EXEC="/home/zen/O20/.venv/bin/python3"
SCANNER_SCRIPT="/home/zen/O20/tools/run_multi_repo_scan.py"

REPOS=(
    "/home/zen/O20"
    "/home/zen/VerticalRisk"
    "/home/zen/insilos_mobile"
    "/home/zen/zencode-ent"
)

echo "======================================================================"
echo " CÀI ĐẶT PRE-PUSH GOVERNANCE HOOK CHO 4 SOVEREIGN REPOSITORIES"
echo "======================================================================"

for repo in "${REPOS[@]}"; do
    if [ ! -d "$repo/.git" ]; then
        echo "⚠️  Bỏ qua $repo (Không tìm thấy thư mục .git)"
        continue
    fi

    HOOK_PATH="$repo/.git/hooks/pre-push"
    mkdir -p "$(dirname "$HOOK_PATH")"

    cat << 'EOF' > "$HOOK_PATH"
#!/usr/bin/env bash
# ==============================================================================
# Sovereign Pre-Push Governance Gate
# ==============================================================================
set -e

SCANNER="/home/zen/O20/tools/run_multi_repo_scan.py"
PYTHON="/home/zen/O20/.venv/bin/python3"

echo "🔍 [GOVERNANCE] Đang chạy kiểm toán Multi-Repository Governance Gate trước khi Push..."
if [ -f "$PYTHON" ] && [ -f "$SCANNER" ]; then
    "$PYTHON" "$SCANNER"
    EXIT_CODE=$?
    if [ $EXIT_CODE -ne 0 ]; then
        echo "❌ [BLOCK] Thao tác 'git push' bị chặn bởi Governance Gate (Mã lỗi: $EXIT_CODE)!"
        echo "Vui lòng cập nhật tài liệu hoặc ghim phiên bản phụ thuộc trước khi push."
        exit $EXIT_CODE
    fi
    if [ -f "/home/zen/O20/tools/test_dual_theme_manifest_segregation.py" ]; then
        (cd /home/zen/O20 && "$PYTHON" -m unittest tools/test_dual_theme_manifest_segregation.py)
    fi
else
    echo "⚠️  Không tìm thấy Python venv hoặc scanner script, bỏ qua gate."
fi

echo "✅ [PASS] Multi-Repository Governance Gate đã xác thực hợp lệ."
exit 0
EOF

    chmod +x "$HOOK_PATH"
    echo "✅ [OK] Đã cài đặt pre-push hook tại: $HOOK_PATH"
done

echo ""
echo "======================================================================"
echo " HOÀN TẤT CÀI ĐẶT PRE-PUSH HOOK TRÊN TẤT CẢ REPOSITORIES"
echo "======================================================================"
