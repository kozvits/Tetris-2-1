@echo off
title Tetris 2 (ZX Spectrum Clone)

echo ========================================
echo   Tetris 2 - ZX Spectrum Clone (1990)
echo   Fuxoft Style
echo ========================================
echo.

REM Check if Python is installed (try 'py' launcher first, then 'python')
py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
) else (
    python --version >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=python
    ) else (
        echo ERROR: Python not found!
        echo Please install Python 3.x from https://www.python.org/
        echo Make sure to check "Add Python to PATH" during installation.
        echo.
        pause
        exit /b 1
    )
)

echo Using Python: %PYTHON_CMD%
echo.

REM Check if Pygame is installed
%PYTHON_CMD% -c "import pygame" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Pygame dependency...
    %PYTHON_CMD% -m pip install pygame
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Failed to install Pygame!
        echo Please try installing manually:
        echo   %PYTHON_CMD% -m pip install pygame
        echo.
        pause
        exit /b 1
    )
    echo Pygame installed successfully!
) else (
    echo Pygame is already installed.
)

echo.
echo Starting game...
echo.
%PYTHON_CMD% tetris2.py

if %errorlevel% neq 0 (
    echo.
    echo Game exited with error.
    pause
)
