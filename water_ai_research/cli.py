"""Offline entry points for the demo and explicit-file manifest verification."""

import argparse
import json
from pathlib import Path

from .audit import verify_manifest
from .demo import run_demo


def main() -> None:
    parser = argparse.ArgumentParser(prog="water-ai")
    commands = parser.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="run the synthetic, offline example")
    demo.add_argument("--output", default="outputs/demo")
    verify = commands.add_parser("verify", help="verify a demo output manifest")
    verify.add_argument("directory")
    args = parser.parse_args()
    if args.command == "demo":
        print(json.dumps(run_demo(args.output), ensure_ascii=False, indent=2, allow_nan=False))
    else:
        root = Path(args.directory)
        verify_manifest(root, json.loads((root / "manifest.json").read_text(encoding="utf-8")))
        print("Manifest verified.")
