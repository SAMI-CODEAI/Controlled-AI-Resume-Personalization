#!/bin/bash
# Compile LaTeX file securely with no shell escape
# Usage: compile-latex.sh <input.tex> <output-dir>
set -euo pipefail

INPUT_FILE="$1"
OUTPUT_DIR="${2:-/output}"

if [ ! -f "$INPUT_FILE" ]; then
    echo "ERROR: Input file not found: $INPUT_FILE" >&2
    exit 1
fi

BASENAME=$(basename "$INPUT_FILE" .tex)

# Run pdflatex with security restrictions
# --no-shell-escape prevents arbitrary command execution
# -interaction=nonstopmode prevents interactive prompts
pdflatex \
    --no-shell-escape \
    -interaction=nonstopmode \
    -output-directory="$OUTPUT_DIR" \
    "$INPUT_FILE" 2>&1

# Run twice for references
pdflatex \
    --no-shell-escape \
    -interaction=nonstopmode \
    -output-directory="$OUTPUT_DIR" \
    "$INPUT_FILE" 2>&1

# Check if PDF was generated
if [ -f "$OUTPUT_DIR/$BASENAME.pdf" ]; then
    echo "SUCCESS: $OUTPUT_DIR/$BASENAME.pdf"
else
    echo "ERROR: PDF generation failed" >&2
    exit 1
fi
