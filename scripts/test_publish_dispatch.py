import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.publish import dispatch

run_id = "20251229_221050"  # <-- remplace par ton run existant
package_dir = PROJECT_ROOT / "data" / "out" / run_id
package_path = package_dir / "post_package.json"

pkg = json.loads(package_path.read_text(encoding="utf-8"))

dispatch(pkg, package_dir=package_dir, dry_run=True, platform_filter="reddit")

