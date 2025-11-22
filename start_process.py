#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для автоматической установки браузеров Playwright и запуска API сервера
"""

import subprocess
import sys
import os


def run_command(command, description):
    """
    Выполняет команду и выводит результат
    
    Args:
        command: Команда для выполнения (список аргументов)
        description: Описание команды для вывода
    """
    print(f"\n{'='*60}")
    print(f"Выполняется: {description}")
    print(f"Команда: {' '.join(command)}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )
        
        if result.stdout:
            print(result.stdout)
        
        print(f"\n✓ {description} выполнено успешно\n")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Ошибка при выполнении: {description}")
        print(f"Код возврата: {e.returncode}")
        if e.stdout:
            print(f"Вывод:\n{e.stdout}")
        if e.stderr:
            print(f"Ошибки:\n{e.stderr}")
        return False
    except FileNotFoundError:
        print(f"\n✗ Команда не найдена: {command[0]}")
        print("Убедитесь, что Playwright установлен: pip install playwright")
        return False


def install_playwright_browsers():
    """
    Устанавливает браузеры для Playwright
    
    Returns:
        True если установка прошла успешно, False в противном случае
    """
    # Определяем, какой браузер устанавливать
    # Можно установить только chromium для экономии места, или все браузеры
    
    # Устанавливаем только chromium (рекомендуется для серверов)
    print("\nУстановка браузеров Playwright...")
    print("Устанавливается Chromium (для работы в headless режиме)")
    
    # Пробуем установить chromium
    success = run_command(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        "Установка Chromium для Playwright"
    )
    
    if not success:
        # Если не получилось, пробуем установить все браузеры
        print("\nПопытка установить все браузеры...")
        success = run_command(
            [sys.executable, "-m", "playwright", "install"],
            "Установка всех браузеров для Playwright"
        )
    
    return success


def install_system_dependencies():
    """
    Устанавливает системные зависимости для Playwright (только для Linux)
    
    Returns:
        True если установка прошла успешно или не требуется, False в противном случае
    """
    # Проверяем, что мы на Linux
    if sys.platform != "linux":
        print("\nСистемные зависимости требуются только для Linux")
        return True
    
    print("\nПопытка установить системные зависимости для Playwright...")
    print("(Это может потребовать прав sudo)")
    
    # Пробуем установить зависимости
    success = run_command(
        [sys.executable, "-m", "playwright", "install-deps", "chromium"],
        "Установка системных зависимостей для Playwright"
    )
    
    return success


def start_api_server():
    """
    Запускает API сервер
    
    Returns:
        Код возврата процесса сервера
    """
    print(f"\n{'='*60}")
    print("Запуск API сервера...")
    print(f"{'='*60}\n")
    
    api_server_path = os.path.join(os.path.dirname(__file__), "api_server.py")
    
    if not os.path.exists(api_server_path):
        print(f"✗ Файл {api_server_path} не найден!")
        return 1
    
    try:
        # Запускаем сервер (он будет работать до прерывания)
        subprocess.run([sys.executable, api_server_path], check=True)
    except KeyboardInterrupt:
        print("\n\nСервер остановлен пользователем")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Ошибка при запуске сервера: {e}")
        return e.returncode
    except Exception as e:
        print(f"\n✗ Неожиданная ошибка: {e}")
        return 1


def main():
    """Главная функция"""
    print("\n" + "="*60)
    print("Real Estate Parser - Автоматическая установка и запуск")
    print("="*60)
    
    # Шаг 1: Установка системных зависимостей (только для Linux)
    if sys.platform == "linux":
        print("\n[Шаг 1/3] Установка системных зависимостей...")
        install_system_dependencies()
    else:
        print("\n[Шаг 1/3] Пропуск системных зависимостей (не Linux)")
    
    # Шаг 2: Установка браузеров Playwright
    print("\n[Шаг 2/3] Установка браузеров Playwright...")
    if not install_playwright_browsers():
        print("\n⚠ Предупреждение: Не удалось установить браузеры Playwright")
        print("Попробуйте выполнить вручную: playwright install chromium")
        response = input("\nПродолжить запуск сервера? (y/n): ")
        if response.lower() != 'y':
            print("Запуск отменен")
            return 1
    
    # Шаг 3: Запуск API сервера
    print("\n[Шаг 3/3] Запуск API сервера...")
    return start_api_server()


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nПрервано пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

