@echo off
REM Copies the PROJECT_OVERVIEW.md content to the Windows clipboard
clip < "%~dp0PROJECT_OVERVIEW.md"
echo Copied PROJECT_OVERVIEW.md to clipboard.
