@ECHO OFF
@REM Save current execution policy
powershell -Command Get-ExecutionPolicy -Scope CurrentUser >temp.txt
set /p OEXP=<temp.txt
del temp.txt

@REM Temporary set unrestricted policy for the current use
powershell -Command Set-ExecutionPolicy -Scope CurrentUser unrestricted

@REM Run the setup powershell script
powershell -File scripts\windows.ps1

@REM Restore the original execution policy
powershell -Command Set-ExecutionPolicy -Scope CurrentUser %OEXP%
