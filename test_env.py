import os
import time

print("=== WAITING FOR ENV VARS ===")
time.sleep(2)  # Даем время Railway обновить переменные

print(f"BOT_TOKEN exists: {'BOT_TOKEN' in os.environ}")
if 'BOT_TOKEN' in os.environ:
    token = os.environ['BOT_TOKEN']
    print(f"BOT_TOKEN length: {len(token)}")
    print(f"BOT_TOKEN first 20 chars: {token[:20]}")
    print(f"BOT_TOKEN contains ':': {':' in token}")
else:
    print("Available variables:")
    for key in sorted(os.environ.keys()):
        print(f"  {key}")
