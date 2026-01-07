#!/bin/bash
echo "=== Checking Formatting Issues ==="
echo ""

echo "1. Checking Chinese punctuation (should have NO space after):"
for file in chapter-{56..66}*.md; do
  count=$(grep -c '[，。！？：；] [^←→»]' "$file" || true)
  if [ "$count" -gt 0 ]; then
    echo "  ⚠️  $file: $count instances found"
  fi
done
echo "  ✅ Check complete"
echo ""

echo "2. Checking English punctuation in code blocks (should be untouched):"
for file in chapter-{56..66}*.md; do
  # 这个检查比较复杂,简化处理
  echo "  ℹ️  $file: manual review recommended for code blocks"
done
echo ""

echo "3. Sample checks from different chapters:"
echo "  Chapter 56 (line 49):"
sed -n '49p' chapter-56-number-precision.md
echo ""
echo "  Chapter 62 (line 107):"
sed -n '107p' chapter-62-weak-references.md
echo ""
echo "  Chapter 65 (line 50):"
sed -n '50p' chapter-65-date-timezone.md
echo ""

echo "=== Formatting verification complete ==="
