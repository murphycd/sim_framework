import re
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.error import HTTPError, URLError
from packaging.version import Version, InvalidVersion
from packaging.specifiers import SpecifierSet
import argparse

REQUIREMENTS_PATH = Path("requirements.txt")
DOCS_PATH = Path("docs")
DOC_FILE_EXT = "py.txt"


def validate_installed_versions(requirements: list[tuple[str, str]]) -> None:
    """
    Verifies that each requirement is currently installed with the pinned
    version. Issues a warning if mismatches are detected.
    """
    try:
        installed = {
            line.split("==")[0].lower(): line.split("==")[1]
            for line in subprocess.check_output(
                ["pip", "freeze"], text=True
            ).splitlines()
            if "==" in line
        }
    except subprocess.CalledProcessError:
        print("Warning: Failed to query installed pip packages.")
        return

    for req, _ in requirements:
        if "==" not in req:
            continue  # Skip non-pinned entries
        name, pinned_version = req.split("==", 1)
        installed_version = installed.get(name.lower())
        if installed_version != pinned_version:
            print(
                f"Warning: {name} pinned to {pinned_version}, \
                    but {installed_version or 'not installed'} is installed."
            )


def parse_requirements(path: Path) -> list[tuple[str, str]]:
    """
    Parses non-comment requirement lines into (requirement, comment) pairs.
    """
    requirements: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        # Split on first comment
        parts = stripped.split("#", 1)
        dep = parts[0].strip()
        comment = parts[1].strip() if len(parts) > 1 else ""

        requirements.append((dep, comment))
    return requirements


def check_metadata_comments(reqs: list[tuple[str, str]]) -> list[str]:
    """
    Returns original requirement strings missing required metadata comments.
    """
    missing: list[str] = []
    for dep, comment in reqs:
        if "[AI_KNOWN]" not in comment and "[DOC_SCRAPE]:" not in comment:
            missing.append(f"{dep}  # {comment}" if comment else dep)
    return missing


def extract_doc_scrape_urls(reqs: list[tuple[str, str]]) -> \
        list[tuple[str, str]]:
    """
    Extracts (package, url) pairs for lines containing DOC_SCRAPE metadata.
    """
    urls: list[tuple[str, str]] = []
    for name, comment in reqs:
        if "[DOC_SCRAPE]:" in comment:
            parts = comment.split("[DOC_SCRAPE]:", 1)
            url = parts[1].strip()
            if url:
                urls.append((name.split("==")[0], url))
    return urls


def verify_url_accessible(url: str, retries: int = 1) -> bool:
    """
    Checks whether the given URL is reachable, with optional retry.
    """
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
        _ = subprocess.check_output(
            ["pip", "install", "pip==junkversion"],
            stderr=subprocess.STDOUT,
            text=True
        )
    except subprocess.CalledProcessError as e:
        version_matches = re.findall(r"\d+\.\d+\.\d+", e.output)
        stable_versions = [
            v for v in version_matches if not Version(v).is_prerelease]
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


def get_installed_packages() -> dict[str, str]:
    try:
        installed = {
            line.split("==")[0].lower(): line.split("==")[1]
            for line in subprocess.check_output(
                ["pip", "freeze"], text=True
            ).splitlines()
            if "==" in line
        }
        return installed
    except subprocess.CalledProcessError:
        return {}


def parse_specifier(requirement: str) -> tuple[str, str | None]:
    """
    Extracts package name and version specifier (e.g., '>=1.2.3') or None.
    """
    match = re.match(r"^([a-zA-Z0-9_\-]+)([=<>!~].*)?$", requirement)
    if match:
        name = match.group(1)
        spec = match.group(2)
        return name, spec
    return requirement, None


def is_valid_doc_file(path: Path) -> tuple[bool, str]:
    """Returns (True, "") if the doc file appears readable and non-empty.
    Returns (False, error message) if not.
    """
    try:
        text = path.read_text(encoding="utf-8")
        if len(text.strip()) == 0:
            return False, "file is empty"
        if "def " not in text or "class " not in text:
            return False, "no recognizable function or class definitions"
        return True, ""
    except Exception as e:
        return False, str(e)


def validate_doc_scrape_targets(reqs: list[tuple[str, str]]) -> \
        tuple[list[str], list[str]]:
    """
    Validates .py.txt doc filenames for [DOC_SCRAPE] packages.
    Returns:
        - errors: list of missing or mismatched docs
        - warnings: list of fallback matches (e.g. matched installed version)
    """
    installed = get_installed_packages()
    errors: list[str] = []
    warnings: list[str] = []

    for dep, comment in reqs:
        if "[DOC_SCRAPE]:" not in comment:
            continue

        name, spec = parse_specifier(dep)
        base = name.lower()
        docs_glob = DOCS_PATH.glob(f"{base}-*.{DOC_FILE_EXT}")

        matched = False

        if spec:
            try:
                spec_set = SpecifierSet(spec)
                for f in docs_glob:
                    vstr = f.stem[len(base) + 1:]
                    try:
                        version = Version(vstr)
                        if version in spec_set:
                            valid, err = is_valid_doc_file(f)
                            if valid:
                                matched = True
                                break
                            else:
                                errors.append(
                                    f"{base} (invalid doc file in {f.name}: {err})")
                    except InvalidVersion:
                        continue
            except Exception:
                continue
        else:
            for f in docs_glob:
                valid, err = is_valid_doc_file(f)
                if valid:
                    matched = True
                    break
                else:
                    errors.append(
                        f"{base} (invalid doc file in {f.name}: {err})")

        if matched:
            continue

        installed_version = installed.get(base)
        if installed_version:
            fallback_path = DOCS_PATH / \
                f"{base}-{installed_version}.{DOC_FILE_EXT}"
            if fallback_path.exists():
                valid, err = is_valid_doc_file(fallback_path)
                if valid:
                    warnings.append(
                        f"{base} (matched installed version {installed_version})")
                    continue
                else:
                    errors.append(
                        f"{base} (fallback doc file invalid: {fallback_path.name}: {err})")
                    continue

        errors.append(f"{base} (missing or version mismatch)")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings as well as errors"
    )
    args = parser.parse_args()

    if not REQUIREMENTS_PATH.exists():
        print("requirements.txt not found.")
        return 1

    requirements = parse_requirements(REQUIREMENTS_PATH)
    summary: list[str] = []
    fatal = False

    # Metadata check
    missing = check_metadata_comments(requirements)
    if missing:
        summary.append("Missing metadata in the following lines:")
        for line in missing:
            summary.append(f"  - {line}")
        summary.append(
            "Each requirement must include [AI_KNOWN] or [DOC_SCRAPE]: <url>")
        fatal = True

    # DOC_SCRAPE validation
    doc_errors, doc_warnings = validate_doc_scrape_targets(requirements)
    if doc_errors:
        summary.append("Missing or invalid documentation for:")
        for item in doc_errors:
            summary.append(f"  - {item}")
        summary.append(
            f"Ensure minified .{DOC_FILE_EXT} docs exist in the docs/ folder.")
        summary.append(
            "Documentation missing for some [DOC_SCRAPE] requirements.")
        fatal = True
    if doc_warnings:
        summary.append(
            "Warning: Docs matched installed version but not pinned:")
        for item in doc_warnings:
            summary.append(f"  - {item}")

    # pip version validation
    pinned = extract_pinned_pip_version(requirements)
    if pinned:
        current = get_installed_pip_version()
        if current != pinned:
            summary.append(
                f"Warning: pip is pinned to {pinned}, \
                    but installed version is {current}"
            )
        latest = get_latest_pip_version()
        if latest and latest != pinned:
            summary.append(
                f"Note: pip {latest} is available. \
                    You may want to update the pinned version."
            )

    if summary:
        print("\nSummary of issues and warnings:")
        for item in summary:
            print("  -", item)
        if fatal or args.strict:
            print("Project validation failed.")
            return 1
        print("Project validation passed with warnings.")
    else:
        print("requirements.txt metadata is valid.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
