@echo off
setlocal enabledelayedexpansion

:: Set UTF-8 encoding
chcp 65001 >nul

:: Set title
title Vidnoz Site Automation Tool

:: Initialize variables
set "PYTHON_CMD=python vidnoz_automation.py sites.json"
set "OPTION_TYPE=all"
set "SITE_SELECTION="
set "GLOBAL_UPDATE="

:main_menu
cls
echo ==============================
echo   Vidnoz Site Automation Tool
echo ==============================
echo.
echo Please select an operation:
echo [1] Process all sites
echo [2] Select specific sites to process (Include)
echo [3] Exclude specific sites (Exclude)
echo [4] Set update mode
echo [5] View current settings
echo [6] Execute command
echo [7] Exit
echo.
set /p choice=Enter option (1-7): 

if "%choice%"=="1" goto process_all
if "%choice%"=="2" goto include_sites
if "%choice%"=="3" goto exclude_sites
if "%choice%"=="4" goto update_mode
if "%choice%"=="5" goto show_settings
if "%choice%"=="6" goto execute_command
if "%choice%"=="7" goto exit_script
goto main_menu

:process_all
cls
echo.
echo Selected to process all sites
set "OPTION_TYPE=all"
set "SITE_SELECTION="
timeout /t 2 >nul
goto main_menu

:include_sites
cls
echo.
echo === Available Sites ===
echo en  - English site
echo jp  - Japanese site
echo it  - Italian site
echo fr  - French site
echo de  - German site
echo ar  - Arabic site
echo pt  - Portuguese site
echo es  - Spanish site
echo kr  - Korean site
echo nl  - Dutch site
echo tr  - Turkish site
echo tw  - Traditional Chinese site
echo.
echo Enter site codes to process, separate multiple sites with commas (example: tw,en,jp)
echo.
set /p SITE_SELECTION=Enter site codes: 
set "OPTION_TYPE=include"
echo.
echo Selected to process these sites: %SITE_SELECTION%
timeout /t 2 >nul
goto main_menu

:exclude_sites
cls
echo.
echo === Available Sites ===
echo en  - English site
echo jp  - Japanese site
echo it  - Italian site
echo fr  - French site
echo de  - German site
echo ar  - Arabic site
echo pt  - Portuguese site
echo es  - Spanish site
echo kr  - Korean site
echo nl  - Dutch site
echo tr  - Turkish site
echo tw  - Traditional Chinese site
echo.
echo Enter site codes to exclude, separate multiple sites with commas (example: jp,kr)
echo.
set /p SITE_SELECTION=Enter site codes: 
set "OPTION_TYPE=exclude"
echo.
echo Selected to exclude these sites: %SITE_SELECTION%
timeout /t 2 >nul
goto main_menu

:update_mode
cls
echo.
echo Select update mode:
echo [1] Basic update mode (update public style only)
echo [2] Global refresh mode (process all pages and buttons)
echo.
set /p update_choice=Enter option (1-2): 

if "%update_choice%"=="1" (
    set "GLOBAL_UPDATE=false"
    echo Selected basic update mode
) else if "%update_choice%"=="2" (
    set "GLOBAL_UPDATE=true"
    echo Selected global refresh mode
) else (
    echo Invalid option, please try again
    timeout /t 2 >nul
    goto update_mode
)
timeout /t 2 >nul
goto main_menu

:show_settings
cls
echo.
echo === Current Settings ===
echo.

if "%OPTION_TYPE%"=="all" (
    echo Site selection: Process all sites
) else if "%OPTION_TYPE%"=="include" (
    echo Site selection: Process only %SITE_SELECTION%
) else if "%OPTION_TYPE%"=="exclude" (
    echo Site selection: Exclude %SITE_SELECTION%
)

if "%GLOBAL_UPDATE%"=="true" (
    echo Update mode: Global refresh (process all pages and buttons)
) else (
    echo Update mode: Basic update (update public style only)
)

echo.
echo Final command:
call :generate_command
echo %FINAL_CMD%

echo.
echo Press any key to continue...
pause >nul
goto main_menu

:execute_command
cls
echo.
echo === Execute Command ===
echo.

:: Generate final command
call :generate_command

:: Modify EXECUTE_MULTI_PAGE_UPDATE variable if needed
if "%GLOBAL_UPDATE%"=="true" (
    echo Temporarily modifying code to enable global refresh mode...
    powershell -NoProfile -Command "(Get-Content vidnoz_automation.py) -replace 'EXECUTE_MULTI_PAGE_UPDATE = False', 'EXECUTE_MULTI_PAGE_UPDATE = True' | Set-Content vidnoz_automation.py.tmp"
    move /y vidnoz_automation.py.tmp vidnoz_automation.py >nul
) else if "%GLOBAL_UPDATE%"=="false" (
    echo Temporarily modifying code to disable global refresh mode...
    powershell -NoProfile -Command "(Get-Content vidnoz_automation.py) -replace 'EXECUTE_MULTI_PAGE_UPDATE = True', 'EXECUTE_MULTI_PAGE_UPDATE = False' | Set-Content vidnoz_automation.py.tmp"
    move /y vidnoz_automation.py.tmp vidnoz_automation.py >nul
)

echo Executing command: %FINAL_CMD%
echo.
echo Press any key to start execution...
pause >nul
echo.
echo Executing, please wait...
echo ==============================

:: Execute command
%FINAL_CMD%

echo.
echo ==============================
echo Command execution completed
echo.
echo Press any key to continue...
pause >nul
goto main_menu

:generate_command
set "FINAL_CMD=%PYTHON_CMD%"

if "%OPTION_TYPE%"=="include" (
    set "FINAL_CMD=%FINAL_CMD% --include=%SITE_SELECTION%"
) else if "%OPTION_TYPE%"=="exclude" (
    set "FINAL_CMD=%FINAL_CMD% --exclude=%SITE_SELECTION%"
)
exit /b

:exit_script
cls
echo.
echo Exiting...
echo Thank you for using the Vidnoz Site Automation Tool!
timeout /t 2 >nul
exit

endlocal 