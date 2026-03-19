#!/usr/bin/env bash

###############################################################################
# OCR-Universal - Pipeline Menu
# Author: Georges Nassopoulos
# Version: 1.0.0
# Description:
#   CLI menu to run the main OCR Universal workflows:
#   - convert one file into extracted text
#   - convert all supported files in a directory
#   - print extracted text to terminal instead of saving
#   - run unit tests
#   - run FastAPI service
#   - validate configuration
#   - run dry-run mode
###############################################################################

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "=============================================="
echo " OCR-Universal - Pipeline Menu"
echo "=============================================="
echo "Project root: ${PROJECT_ROOT}"
echo ""

## ---------------------------------------------------------------------------
## Helpers
## ---------------------------------------------------------------------------

pause() {
  read -rp "Press ENTER to continue..."
}

run_python() {
  echo ""
  echo ">>> $*"
  $PYTHON_BIN "$@"
}

## ---------------------------------------------------------------------------
## Menu
## ---------------------------------------------------------------------------

while true; do
  echo ""
  echo "Select an action:"
  echo " 1) Validate config"
  echo " 2) Dry-run"
  echo " 3) Convert one file"
  echo " 4) Convert one directory"
  echo " 5) Convert one file and print output"
  echo " 6) Convert one directory and print output"
  echo " 7) Run tests"
  echo " 8) Run API"
  echo " 9) Show help"
  echo "10) Show version"
  echo " 0) Exit"
  echo ""

  read -rp "Your choice: " choice

  case "$choice" in
    1)
      run_python main.py --validate-config
      pause
      ;;
    2)
      run_python main.py --dry-run
      pause
      ;;
    3)
      read -rp "Input file path [default: ./data/input]: " INPUT_PATH
      INPUT_PATH="${INPUT_PATH:-./data/input}"

      run_python main.py --mode convert --path "$INPUT_PATH"
      pause
      ;;
    4)
      read -rp "Input directory path [default: ./data/input]: " INPUT_PATH
      INPUT_PATH="${INPUT_PATH:-./data/input}"

      run_python main.py --mode convert --path "$INPUT_PATH"
      pause
      ;;
    5)
      read -rp "Input file path [default: ./data/input]: " INPUT_PATH
      INPUT_PATH="${INPUT_PATH:-./data/input}"

      run_python main.py --mode convert --path "$INPUT_PATH" --print
      pause
      ;;
    6)
      read -rp "Input directory path [default: ./data/input]: " INPUT_PATH
      INPUT_PATH="${INPUT_PATH:-./data/input}"

      run_python main.py --mode convert --path "$INPUT_PATH" --print
      pause
      ;;
    7)
      run_python main.py --mode test
      pause
      ;;
    8)
      run_python main.py --mode api
      pause
      ;;
    9)
      run_python main.py --help
      pause
      ;;
    10)
      run_python main.py --version
      pause
      ;;
    0)
      echo "Bye"
      exit 0
      ;;
    *)
      echo "Invalid choice."
      pause
      ;;
  esac
done