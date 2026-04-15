@echo off
REM AI Employee Vault CLI - Easy wrapper
REM Usage: vault list, vault status, vault read <file>, etc.

cd /d "%~dp0"
python scripts\vault_cli.py %*
