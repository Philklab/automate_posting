import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def main():
    input_dir = Path(os.getenv("INPUT_DIR", "./data/in"))
    output_dir = Path(os.getenv("OUTPUT_DIR", "./data/out"))

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_out = output_dir / run_id
    run_out.mkdir(parents=True, exist_ok=True)

    print("=== DRY RUN ===")
    print(f"Input:  {input_dir.resolve()}")
    print(f"Output: {run_out.resolve()}")

    if not input_dir.exists():
        print("No input folder found. Create it and add assets.")
        return

    files = list(input_dir.glob("*"))
    print(f"Found {len(files)} file(s):")
    for f in files:
        print(" -", f.name)

    print("\nNext step: generate a post-package.json here, and later call platform adapters.")

if __name__ == "__main__":
    main()
