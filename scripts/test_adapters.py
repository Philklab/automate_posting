import json
import sys
from pathlib import Path

# Add project root to sys.path so "src" becomes importable
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.adapters.youtube import run as youtube_run
from src.adapters.reddit import run as reddit_run
from src.adapters.instagram import run as instagram_run

# Put the exact run folder here:
RUN_DIR = PROJECT_ROOT / "data" / "out" / "20251229_221050"  # <-- change if different

package_path = RUN_DIR / "post_package.json"
package = json.loads(package_path.read_text(encoding="utf-8"))

print("TOP KEYS:", list(package.keys()))
print("TARGETS:", package.get("targets"))
print("PLATFORMS:", package.get("platforms"))

# Helps adapters resolve relative media paths
package["package_dir"] = str(RUN_DIR)

youtube_run(package, dry_run=True)
reddit_run(package, dry_run=True)
instagram_run(package, dry_run=True)
