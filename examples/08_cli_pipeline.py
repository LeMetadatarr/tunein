"""08_cli_pipeline.py — drive the tunein CLI from Python via subprocess.

The CLI entry point is `tunein` (see pyproject.toml [project.scripts]).
This script shows how to use it in a shell pipeline from Python.

Run:
    python examples/08_cli_pipeline.py
"""

import json
import subprocess
import sys


def cli_search(query: str) -> list[dict]:
    """Run `tunein search <query> --format json` and return parsed results."""
    result = subprocess.run(
        ["tunein", "search", query, "--format", "json"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"CLI error: {result.stderr.strip()}", file=sys.stderr)
        return []
    return json.loads(result.stdout)


def main():
    query = "Radio Paradise"
    print(f"Searching for: {query!r}\n")

    stations = cli_search(query)
    if not stations:
        print("No results.")
        return

    # Sort by bitrate.
    stations.sort(key=lambda x: x.get("bit_rate") or 0, reverse=True)

    print(f"{'Title':40s}  {'kbps':>5}  {'Codec':6s}  URL")
    print("-" * 90)
    for s in stations[:5]:
        print(
            f"{s['title']:40s}"
            f"  {str(s.get('bit_rate', '?')):>5}"
            f"  {s.get('media_type', '?'):6s}"
            f"  {s.get('stream', '')}"
        )


if __name__ == "__main__":
    main()
