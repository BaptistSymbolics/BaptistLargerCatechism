#!/bin/bash
# Baptist Larger Catechism Theological Consistency Review
#
# This script loops through each question of the Baptist Larger Catechism
# and uses Claude Code to compare it against:
#   - The Baptist Shorter Catechism (primary standard)
#   - The 1689 Second London Baptist Confession (primary standard)
#   - The Westminster Larger Catechism (solidarity reference)
#
# Usage:
#   ./scripts/run-comparison.sh              # Run all 191 questions
#   ./scripts/run-comparison.sh 1 10         # Run questions 1-10
#   ./scripts/run-comparison.sh 50 50        # Run just question 50
#
# The script is resumable -- it skips questions that already have
# an analysis file. Delete analysis/qNNN-comparison.md to re-run.
#
# Prerequisites:
#   - claude CLI installed and authenticated
#   - Reference texts in references/ directory

set -euo pipefail

cd "$(dirname "$0")/.."

# Trap Ctrl-C and clean up
CLAUDE_PID=""
cleanup() {
    echo ""
    echo "Interrupted. Cleaning up..."
    if [ -n "$CLAUDE_PID" ] && kill -0 "$CLAUDE_PID" 2>/dev/null; then
        kill "$CLAUDE_PID" 2>/dev/null
        wait "$CLAUDE_PID" 2>/dev/null || true
    fi
    echo "Stopped at question $CURRENT_Q. Re-run to resume from where you left off."
    exit 130
}
trap cleanup INT TERM

# Range arguments (default: all 191)
START=${1:-1}
END=${2:-191}

ANALYSIS_DIR="analysis"
mkdir -p "$ANALYSIS_DIR"

echo "=========================================="
echo "Baptist Larger Catechism Consistency Review"
echo "Questions $START through $END"
echo "Press Ctrl-C to stop (resumable)"
echo "=========================================="
echo ""

# Track summary stats
CONSISTENT=0
MINOR=0
SIGNIFICANT=0
ERRORS=0
CURRENT_Q=0

for i in $(seq "$START" "$END"); do
    CURRENT_Q=$i

    # Zero-pad the filename
    PADDED=$(printf "%03d" "$i")
    TOML_FILE="src/${PADDED}.toml"
    OUTPUT_FILE="${ANALYSIS_DIR}/q${PADDED}-comparison.md"

    # Skip if already analyzed (for resumability)
    if [ -f "$OUTPUT_FILE" ]; then
        echo "[$PADDED/191] Already analyzed, skipping."
        # Still count it in stats
        VERDICT=$(grep -m1 "^## Verdict:" "$OUTPUT_FILE" 2>/dev/null | sed 's/## Verdict: //' || echo "UNKNOWN")
        case "$VERDICT" in
            *CONSISTENT*) CONSISTENT=$((CONSISTENT + 1)) ;;
            *MINOR*) MINOR=$((MINOR + 1)) ;;
            *SIGNIFICANT*) SIGNIFICANT=$((SIGNIFICANT + 1)) ;;
        esac
        continue
    fi

    if [ ! -f "$TOML_FILE" ]; then
        echo "[$PADDED/191] TOML file not found, skipping."
        continue
    fi

    echo "[$PADDED/191] Analyzing question $i..."

    # Read the TOML content for inclusion in the prompt
    TOML_CONTENT=$(cat "$TOML_FILE")

    # Build the prompt for Claude
    PROMPT="Analyze Baptist Larger Catechism question $i for theological consistency.

Here is the BLC question content:
\`\`\`toml
$TOML_CONTENT
\`\`\`

## Theological Framework

The BLC is a recent creation meant to align with and exposit the 1689 Baptist Confession and the Baptist Shorter Catechism (primary authoritative standards), while showing solidarity with the Westminster Larger Catechism in modernized form.

## What to Look For (in order of severity)

1. OMISSIONS: Key doctrinal elements, conditions, or qualifications present in the 1689/Shorter that the BLC drops. Omissions are as serious as contradictions.
2. STRUCTURAL CHANGES: Rearrangements of theological relationships that alter meaning (e.g., changing faith from the instrument of reception to a separate mechanism).
3. CONTRADICTIONS: Direct theological conflict with the standards.

## Steps

1. Read references/shorter-catechism.txt and find the parallel question(s). Quote the Shorter's answer in full. Compare theology, noting agreement, expansion, OMISSIONS of key phrases/qualifications, and structural changes to how concepts relate.

2. Read references/1689-confession.txt and find the relevant chapter(s)/paragraph(s). Quote the relevant text. Compare theology, noting agreement, expansion, OMISSIONS of key doctrinal elements, and structural changes.

3. Read references/westminster-larger-catechism.txt and find the parallel WLC question(s). Quote the WLC answer. Note structural solidarity, intentional Baptist divergences (baptism, ecclesiology, covenant theology -- expected and acceptable), and unexpected divergences in areas of normal Baptist-Presbyterian agreement. Flag key WLC phrases dropped without theological reason.

4. Render a final verdict:
   - CONSISTENT: Faithfully exposits the 1689/Shorter, preserves all key content, shows appropriate WLC solidarity
   - MINOR CONCERN: Substantially consistent but something worth noting (weakened precision, subtle structural shifts, unexplained WLC divergence)
   - SIGNIFICANT CONCERN: Omits key doctrinal elements from the 1689/Shorter, contradicts standards, restructures theological relationships in doctrine-altering ways, or introduces novelty

5. Write the analysis to ${OUTPUT_FILE} in this format:

# Q${i}: {question text}

## Verdict: {CONSISTENT | MINOR CONCERN | SIGNIFICANT CONCERN}

## Summary
{2-3 sentence summary}

## Shorter Catechism Comparison
**Parallel Question(s):** {quote the FULL parallel Q&A, or 'No direct parallel'}
- Omissions: {key phrases/qualifications from the Shorter missing in the BLC}
- Structural changes: {rearranged theological relationships}
{Other key findings}

## 1689 Confession Comparison
**Relevant Section(s):** {Chapter N, Paragraph N -- quote relevant text}
- Omissions: {key elements from the Confession missing in the BLC}
- Structural changes: {rearranged theological relationships}
{Other key findings}

## Westminster Larger Catechism Comparison
**Parallel Question(s):** {WLC Q number and FULL text}
- Solidarity: {STRONG / MODERATE / WEAK}
- Intentional Baptist divergences: {expected departures}
- Unexpected divergences: {departures in areas of normal agreement}
- Key phrases dropped: {WLC phrases omitted without theological reason}

## Detailed Notes
{Specific observations}

## Scripture Analysis
{Proof text observations}

IMPORTANT: The Shorter Catechism's phrasing is the baseline the BLC should mirror in modernized form. When the Shorter has a direct parallel, the BLC must PRESERVE its core content, not merely avoid contradicting it."

    # Run Claude in background so we can kill it on Ctrl-C
    claude --print --dangerously-skip-permissions \
        "$PROMPT" \
        > /dev/null 2>&1 &
    CLAUDE_PID=$!

    # Wait for Claude to finish
    if wait "$CLAUDE_PID" 2>/dev/null; then
        CLAUDE_PID=""
        # Check the verdict if file was created
        if [ -f "$OUTPUT_FILE" ]; then
            VERDICT=$(grep -m1 "^## Verdict:" "$OUTPUT_FILE" 2>/dev/null | sed 's/## Verdict: //' || echo "UNKNOWN")
            echo "[$PADDED/191] Done - $VERDICT"

            case "$VERDICT" in
                *CONSISTENT*) CONSISTENT=$((CONSISTENT + 1)) ;;
                *MINOR*) MINOR=$((MINOR + 1)) ;;
                *SIGNIFICANT*) SIGNIFICANT=$((SIGNIFICANT + 1)) ;;
            esac
        else
            echo "[$PADDED/191] Warning: No output file generated"
            ERRORS=$((ERRORS + 1))
        fi
    else
        CLAUDE_PID=""
        echo "[$PADDED/191] ERROR: Claude invocation failed"
        ERRORS=$((ERRORS + 1))
    fi
done

# Generate summary report
SUMMARY_FILE="${ANALYSIS_DIR}/SUMMARY.md"
cat > "$SUMMARY_FILE" <<EOF
# Baptist Larger Catechism Consistency Review Summary

**Date:** $(date -u +"%Y-%m-%dT%H:%M:%SZ")
**Range:** Questions $START - $END

## Theological Framework

The Baptist Larger Catechism (BLC) is evaluated against:
- **Primary Standards**: 1689 Second London Baptist Confession, Baptist Shorter Catechism
- **Solidarity Reference**: Westminster Larger Catechism

## Results

| Verdict | Count |
|---------|-------|
| Consistent | $CONSISTENT |
| Minor Concern | $MINOR |
| Significant Concern | $SIGNIFICANT |
| Errors | $ERRORS |
| **Total** | **$((CONSISTENT + MINOR + SIGNIFICANT + ERRORS))** |

## Questions with Concerns

EOF

# List any concerns in the summary
for f in "$ANALYSIS_DIR"/q*-comparison.md; do
    if [ -f "$f" ]; then
        VERDICT=$(grep -m1 "^## Verdict:" "$f" 2>/dev/null | sed 's/## Verdict: //' || echo "UNKNOWN")
        if [[ "$VERDICT" == *"CONCERN"* ]]; then
            TITLE=$(head -1 "$f" | sed 's/^# //')
            SUMMARY_LINE=$(sed -n '/^## Summary/,/^##/p' "$f" | grep -v "^##" | head -3)
            echo "### $TITLE" >> "$SUMMARY_FILE"
            echo "**Verdict:** $VERDICT" >> "$SUMMARY_FILE"
            echo "" >> "$SUMMARY_FILE"
            echo "$SUMMARY_LINE" >> "$SUMMARY_FILE"
            echo "" >> "$SUMMARY_FILE"
        fi
    fi
done

echo ""
echo "=========================================="
echo "REVIEW COMPLETE"
echo "=========================================="
echo "Consistent:         $CONSISTENT"
echo "Minor Concerns:     $MINOR"
echo "Significant:        $SIGNIFICANT"
echo "Errors:             $ERRORS"
echo ""
echo "Full results: $ANALYSIS_DIR/"
echo "Summary:      $SUMMARY_FILE"
