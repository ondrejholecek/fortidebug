@ECHO OFF
@ECHO Preparing environment to initialize the FortiDebug application

@REM Save current execution policy
powershell -Command Get-ExecutionPolicy -Scope CurrentUser >temp.txt
set /p OEXP=<temp.txt
del temp.txt

@REM Temporary set unrestricted policy for the current use
powershell -Command Set-ExecutionPolicy -Scope CurrentUser unrestricted

@REM Run the setup powershell script
powershell -Command Unblock-File -Path scripts\windows.ps1

@ECHO Starting the init script
powershell -File scripts\windows.ps1

@REM Restore the original execution policy
@ECHO Restoring the environment
powershell -Command Set-ExecutionPolicy -Scope CurrentUser %OEXP%
