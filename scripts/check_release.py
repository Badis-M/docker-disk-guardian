"""Validate release intent without creating tags, releases, or files."""

import argparse
import re
import subprocess
import tomllib
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("tag")
    args = parser.parse_args()
    if re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", args.tag) is None:
        parser.error("tag must be a stable version such as v1.0.1")
    project = Path(__file__).resolve().parents[1]
    metadata = project / "pyproject.toml"
    if metadata.exists():
        version = tomllib.loads(metadata.read_text())["project"]["version"]
    else:
        match = re.search(
            r'^(?:readonly )?LSA_VERSION="([0-9.]+)"', (project / "lib/cli.sh").read_text(), re.M
        )
        if match is None:
            raise SystemExit("Cannot determine the CLI version")
        version = match.group(1)
    if args.tag != f"v{version}":
        raise SystemExit("Release tag does not match the declared version")
    if metadata.exists() and (project / "src").exists():
        # Version constants must not diverge from distribution metadata.
        init = next((project / "src").glob("*/__init__.py"))
        match = re.search(r'__version__ = "([0-9.]+)"', init.read_text())
        if match and match.group(1) != version:
            raise SystemExit("Package version constant disagrees with distribution metadata")
    subprocess.run(
        ["git", "rev-parse", "--verify", f"refs/tags/{args.tag}^{{commit}}"],
        check=True,
        cwd=project,
        stdout=subprocess.DEVNULL,
    )
    tagged = subprocess.check_output(
        ["git", "rev-parse", f"refs/tags/{args.tag}^{{commit}}"], cwd=project
    )
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=project)
    if tagged != head:
        raise SystemExit("HEAD must be the exact tagged commit")
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", "HEAD", "origin/main"], check=True, cwd=project
    )
    print(f"Release metadata validated: {args.tag}")


if __name__ == "__main__":
    main()
