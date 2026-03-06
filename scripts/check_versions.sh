#!/bin/bash
echo "============================================"
echo " CryptoQuant AI - Version Checker"
echo "============================================"
for v in "" "3" "3.11" "3.12" "3.13" "3.14"; do
  cmd="python${v}"
  result=$($cmd --version 2>/dev/null)
  [ -n "$result" ] && echo "  $cmd => $result" || echo "  $cmd => not found"
done
echo ""
echo "[Node / npm]"
node --version 2>/dev/null && npm --version 2>/dev/null || echo "  Node not found"
echo "============================================"
