@echo off
chcp 65001 >nul
title Tetris 2 (ZX Spectrum Clone)

echo ========================================
echo   Tetris 2 - ZX Spectrum Clone (1990)
echo   Fuxoft Style
echo ========================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ОШИБКА: Python не найден!
    echo Пожалуйста, установите Python 3.x с https://www.python.org/
    echo.
    pause
    exit /b 1
)

REM Проверка наличия Pygame
python -c "import pygame" >nul 2>&1
if %errorlevel% neq 0 (
    echo Установка зависимости Pygame...
    pip install pygame
    if %errorlevel% neq 0 (
        echo ОШИБКА: Не удалось установить Pygame!
        pause
        exit /b 1
    )
)

echo Запуск игры...
echo.
python tetris2.py

if %errorlevel% neq 0 (
    echo.
    echo Игра завершена с ошибкой.
    pause
)
