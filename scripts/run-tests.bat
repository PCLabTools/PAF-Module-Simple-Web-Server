@echo off
echo Running unit tests for standard_template module...

REM Change to the module directory
cd /d "%~dp0.."

REM Calculate the src root directory
for /f "delims=" %%i in ("..\..\..") do set "SRC_ROOT=%%~fi"

REM Run the tests using Python's unittest discover with proper path setup
python -u -c "import sys; import os; src_root = os.path.dirname(os.path.dirname(os.path.dirname(os.getcwd()))); sys.path.insert(0, src_root); import unittest; loader = unittest.TestLoader(); suite = loader.discover('tests', pattern='test_*.py'); runner = unittest.TextTestRunner(verbosity=2); result = runner.run(suite); sys.exit(0 if result.wasSuccessful() else 1)"

REM Check the exit code
if %errorlevel% equ 0 (
    echo.
    echo All tests passed!
) else (
    echo.
    echo Some tests failed!
)
