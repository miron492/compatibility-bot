import os
print("=== ENV VARS ===")
for key in sorted(os.environ.keys()):
    if 'TOKEN' in key or 'SECRET' in key or 'KEY' in key:
        print(f"{key}: {os.environ[key][:15]}...")
    else:
        print(f"{key}: {os.environ[key][:50]}")
