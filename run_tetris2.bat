@echo off
title Tetris 2 (ZX Spectrum Clone)

echo ========================================
echo   Tetris 2 - ZX Spectrum Clone (1990)
echo   Fuxoft Style
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.x from https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Check if Pygame is installed
python -c "import pygame" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Pygame dependency...
    pip install pygame
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install Pygame!
        pause
        exit /b 1
    )
)

echo Starting game...
echo.
python tetris2.py

if %errorlevel% neq 0 (
    echo.
    echo Game exited with error.
    pause
)
