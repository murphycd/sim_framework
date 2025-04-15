import subprocess
import urllib.request
import time
from urllib.error import URLError, HTTPError
from pathlib import Path
import yaml

import re
import subprocess
from packaging.version import Version  # Ensure this is in your requirements.txt

REQUIREMENTS_PATH = Path("requirements.txt")
DOCS_PATH = Path("docs")


def validate_installed_versions(requirements: list[tuple[str, str]]) -> None:
    """
    Verifies that each requirement is currently installed with the pinned version.
    Issues a warning if mismatches are detected.
    """
    try:
        installed = {
            line.split("==")[0].lower(): line.split("==")[1]
            for line in subprocess.check_output(
                ["pip", "freeze"], text=True
            ).splitlines()
            if "==" in line
        }
    except subprocess.CalledProcessError as e:
        print("Warning: Failed to query installed pip packages.")
        return

    for req, _ in requirements:
        if "==" not in req:
            continue  # Skip non-pinned entries
        name, pinned_version = req.split("==", 1)
        installed_version = installed.get(name.lower())
        if installed_version != pinned_version:
            print(
                f"Warning: {name} pinned to {pinned_version}, but {installed_version or 'not installed'} is installed."
            )


def parse_requirements(path: Path) -> list[tuple[str, str]]:
    """Parses non-comment requirement lines into (requirement, comment) pairs."""
    requirements = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        parts = stripped.split("#", 1)
        dep = parts[0].strip()
        comment = parts[1].strip() if len(parts) > 1 else ""

        requirements.append((dep, comment))
    return requirements


def check_metadata_comments(lines: list[str]) -> list[str]:
    """Returns lines missing required metadata comments."""
    missing = []
    for line in lines:
        if line.strip().startswith("#") or not line.strip():
            continue
        if "[AI_KNOWN]" not in line and "[DOC_SCRAPE]:" not in line:
            missing.append(line)
    return missing


def extract_doc_scrape_urls(reqs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Extracts (package, url) pairs for lines containing DOC_SCRAPE metadata."""
    urls = []
    for name, comment in reqs:
        if "[DOC_SCRAPE]:" in comment:
            parts = comment.split("[DOC_SCRAPE]:", 1)
            url = parts[1].strip()
            if url:
                urls.append((name.split("==")[0], url))
    return urls


def verify_url_accessible(url: str, retries: int = 1) -> bool:
    """Checks whether the given URL is reachable, with optional retry."""
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if 200 <= response.status < 400:
                    return True
        except (HTTPError, URLError, ValueError):
            if attempt < retries:
                time.sleep(1)
    return False


def get_installed_pip_version() -> str:
    output = subprocess.check_output(["pip", "--version"], text=True)
    return output.split()[1]


def get_latest_pip_version() -> str | None:
    """
    Retrieves the latest stable pip version by triggering pip's error message
    and extracting valid semantic versions from it.

    The regex looks for patterns like '23.2.1' (major.minor.patch).
    Filters out pre-release versions (e.g., rc, beta, alpha).
    """
    try:
        output = subprocess.check_output(
            ["pip", "install", "pip==junkversion"], stderr=subprocess.STDOUT, text=True
        )
    except subprocess.CalledProcessError as e:
        version_matches = re.findall(r"\d+\.\d+\.\d+", e.output)
        stable_versions = [v for v in version_matches if not Version(v).is_prerelease]
        if stable_versions:
            sorted_versions = sorted(stable_versions, key=Version)
            return sorted_versions[-1]
    return None


def extract_pinned_pip_version(reqs: list[tuple[str, str]]) -> str | None:
    """Finds the pinned pip version in requirements.txt."""
    for dep, _ in reqs:
        if dep.startswith("pip=="):
            return dep.split("==")[1]
    return None


def validate_doc_scrape_targets(requirements: list[tuple[str, str]]) -> list[str]:
    """Returns a list of packages with [DOC_SCRAPE] metadata whose docs are missing or invalid."""
    missing_or_invalid = []

    for dep, comment in requirements:
        if "[DOC_SCRAPE]:" not in comment:
            continue

        package = dep.split("==")[0]
        doc_path = DOCS_PATH / f"{package}.yaml"

        if not doc_path.exists():
            missing_or_invalid.append(f"{package} (missing)")
            continue

        try:
            with doc_path.open("r", encoding="utf-8") as f:
                yaml.safe_load(f)
        except Exception as e:
            missing_or_invalid.append(f"{package} (invalid YAML: {e})")

    return missing_or_invalid


def main() -> int:
    if not REQUIREMENTS_PATH.exists():
        print("requirements.txt not found.")
        return 1

    requirements = parse_requirements(REQUIREMENTS_PATH)
    summary: list[str] = []

    # Metadata check
    missing = check_metadata_comments(requirements)
    if missing:
        print("Missing metadata in the following lines:")
        for line in missing:
            print("  -", line)
        print("Each requirement must include [AI_KNOWN] or [DOC_SCRAPE]: <url>")
        summary.append("Metadata missing for some requirements.")

    # DOC_SCRAPE validation
    doc_missing = validate_doc_scrape_targets(requirements)
    if doc_missing:
        print("Missing or invalid documentation for:")
        for item in doc_missing:
            print("  -", item)
        print("Ensure minified .md or .yaml docs exist in the docs/ folder.")
        summary.append("Documentation missing for some [DOC_SCRAPE] requirements.")

    # pip version validation
    pinned = extract_pinned_pip_version(requirements)
    if pinned:
        current = get_installed_pip_version()
        if current != pinned:
            print(
                f"Warning: pip is pinned to {pinned}, but installed version is {current}"
            )
            summary.append(
                f"Installed pip version is {current}, but pinned is {pinned}."
            )
        latest = get_latest_pip_version()
        if latest and latest != pinned:
            print(
                f"Note: pip {latest} is available. You may want to update the pinned version."
            )
            summary.append(f"Newer pip version available: {latest}.")

    if summary:
        print("\nSummary of issues and warnings:")
        for item in summary:
            print("  -", item)
        print("Project validation failed.")
        return 1

    print("requirements.txt metadata is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
