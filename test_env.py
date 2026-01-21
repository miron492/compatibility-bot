#!/usr/bin/env python3
import os

print("=== ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ===")
print(f"Все переменные: {list(os.environ.keys())}")
print(f"BOT_TOKEN exists: {'BOT_TOKEN' in os.environ}")
print(f"BOT_TOKEN value (first 20 chars): {os.environ.get('BOT_TOKEN', 'NOT FOUND')[:20] if 'BOT_TOKEN' in os.environ else 'NOT FOUND'}")
print("===================================")

# Также проверим Procfile
print("\n=== ПРОВЕРКА ФАЙЛОВ ===")
import os
print("Список файлов:")
for file in os.listdir('.'):
    print(f"  {file}")
