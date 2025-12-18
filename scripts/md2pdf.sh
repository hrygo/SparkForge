#!/bin/bash

# ========================================================
# Council PDF Engine - CLI Wrapper
# ========================================================

# 1. Resolve the absolute path of the tool
# This ensures the script works no matter which directory you run it from
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
CONVERTER_PATH="$SCRIPT_DIR/pdf_tool/converter.py"

# 2. Python Environment Check
PYTHON_EXEC="python3"
if [ -x "/opt/anaconda3/bin/python3" ]; then
    PYTHON_EXEC="/opt/anaconda3/bin/python3"
fi

# 3. Execution
# Forward all arguments ("$@") to the internal python core
# Set PYTHONPATH to verify imports if needed
"$PYTHON_EXEC" "$CONVERTER_PATH" "$@"

# 4. Exit Code Propagation
exit $?
