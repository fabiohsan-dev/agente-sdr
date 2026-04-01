"""Quick test to verify all routes load correctly."""
import sys
sys.stdout.reconfigure(encoding="utf-8")

from apps.api.main import app

print(f"Total routes: {len(app.routes)}")
for r in app.routes:
    methods = getattr(r, "methods", "MOUNT")
    name = getattr(r, "name", "?")
    path = getattr(r, "path", "?")
    print(f"  {methods} {path} -> {name}")
    
print("\nAll routes loaded successfully!")
