#!/usr/bin/env python3
"""Update a package to a new upstream version.

Bumping a package in this tree means changing three things that have to agree
with each other: the version variable in Makefile.<pkg>, the package's line in
sources/manifest.txt, and the tarball in sources/. This does all three, in an
order that never leaves the tree half-updated: nothing is written until the
tarball has been downloaded and its SHA-256 computed from the bytes that
actually arrived.

    update-package.py --list-packages
    update-package.py --package julia --list-versions
    update-package.py --package julia                  # bump to latest
    update-package.py --package julia --version 1.11.7 # bump to a specific one
    update-package.py --package julia --dry-run        # say what would change

Packages are described in packages.yaml at the top of the tree.

Standard library only, deliberately: this tree builds its own Python, so the
tool that fetches its sources cannot depend on anything installed into it.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_NAME = "packages.yaml"

USER_AGENT = "nlytiq-base-update-package/1.0 (+https://github.com/joelandman/nlytiq-base)"
HTTP_TIMEOUT = 60
HTTP_RETRIES = 3


class Fail(Exception):
    """A fatal, already-explained error. Caught in main(), printed, exit 1."""


def warn(msg):
    print("warning: %s" % msg, file=sys.stderr)


# ---------------------------------------------------------------------------
# Configuration file
#
# packages.yaml uses a small subset of YAML: nested mappings, plain or quoted
# scalars, comments, blank lines. That is little enough to parse here rather
# than depend on PyYAML, which may not be installed -- but if it is installed,
# it is used, so the file is never at the mercy of the parser below.
# ---------------------------------------------------------------------------

_SCALARS = {"true": True, "false": False, "yes": True, "no": False,
            "null": None, "~": None, "": None}


def _parse_scalar(text):
    """Interpret the value half of a 'key: value' line."""
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        body = text[1:-1]
        # Only double quotes take escapes, as in YAML proper.
        if text[0] == '"':
            body = body.encode("utf-8").decode("unicode_escape")
        return body
    # An unquoted value may carry a trailing comment, but only when the '#' is
    # preceded by whitespace -- URLs and regexes contain bare '#' happily.
    cut = re.search(r"\s+#", text)
    if cut:
        text = text[:cut.start()].strip()
    low = text.lower()
    if low in _SCALARS:
        return _SCALARS[low]
    if re.fullmatch(r"-?[0-9]+", text):
        return int(text)
    return text


def parse_simple_yaml(text, filename="<config>"):
    """Parse the mapping-only YAML subset used by packages.yaml."""
    root = {}
    # stack of (indent, mapping); mapping at the top is where keys land
    stack = [(-1, root)]
    pending = None      # (indent, key, parent) for a 'key:' with no value yet

    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if "\t" in raw[:indent]:
            raise Fail("%s:%d: tabs are not valid YAML indentation" % (filename, lineno))
        body = line.strip()

        if body.startswith("- "):
            raise Fail("%s:%d: sequences are not supported by this parser" % (filename, lineno))
        if body.startswith("{") or body.endswith("}"):
            raise Fail("%s:%d: flow mappings ({a: b}) are not supported by this parser"
                       % (filename, lineno))

        m = re.match(r"^([^:]+):(?:\s+(.*))?$", body)
        if not m:
            raise Fail("%s:%d: expected 'key:' or 'key: value', got %r" % (filename, lineno, body))
        key = m.group(1).strip()
        value = m.group(2)

        # A 'key:' with nothing after it opens a nested mapping, but only if
        # the next content line is indented further.
        if pending is not None:
            p_indent, p_key, p_parent = pending
            if indent > p_indent:
                child = {}
                p_parent[p_key] = child
                # Keyed by the indent of the parent key, not of its contents,
                # so the pop below closes the block at the right level.
                stack.append((p_indent, child))
            else:
                p_parent[p_key] = None
            pending = None

        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise Fail("%s:%d: indentation does not line up with any parent key"
                       % (filename, lineno))
        parent = stack[-1][1]

        if value is None or value.strip() == "":
            pending = (indent, key, parent)
        else:
            parent[key] = _parse_scalar(value)

    if pending is not None:
        pending[2][pending[1]] = None
    return root


def load_config(path):
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    try:
        import yaml  # noqa: F401  (optional; better errors and full YAML)
    except ImportError:
        data = parse_simple_yaml(text, path)
    else:
        data = yaml.safe_load(text)

    if not isinstance(data, dict) or "packages" not in data:
        raise Fail("%s: no 'packages:' mapping found" % path)
    packages = data["packages"]
    if not isinstance(packages, dict) or not packages:
        raise Fail("%s: 'packages:' is empty" % path)

    defaults = data.get("defaults") or {}
    for name, spec in packages.items():
        if not isinstance(spec, dict):
            raise Fail("%s: package '%s' is not a mapping" % (path, name))
        for field in ("makefile", "version_var", "filename", "url", "versions"):
            if not spec.get(field):
                raise Fail("%s: package '%s' is missing '%s'" % (path, name, field))
        if not isinstance(spec["versions"], dict):
            raise Fail("%s: package '%s': 'versions' is not a mapping" % (path, name))
    return {
        "sources_dir": defaults.get("sources_dir", "sources"),
        "manifest": defaults.get("manifest", "sources/manifest.txt"),
        "packages": packages,
    }


# ---------------------------------------------------------------------------
# Versions
# ---------------------------------------------------------------------------

# How prerelease markers order among themselves: dev < alpha < beta < rc.
_PRE_ORDER = {"dev": 0, "alpha": 1, "a": 1, "beta": 2, "b": 2,
              "rc": 3, "c": 3, "pre": 3, "preview": 3}

_VERSION_RE = re.compile(
    r"^(?P<release>[0-9]+(?:\.[0-9]+)*)"
    r"(?:[-._]?(?P<pre>[A-Za-z]+)\.?(?P<num>[0-9]+)?)?$"
)


class Version:
    """A comparable version, tolerant of the shapes upstreams actually use."""

    __slots__ = ("text", "release", "pre", "forced_pre")

    def __init__(self, text, forced_pre=False):
        self.text = str(text).strip()
        self.forced_pre = forced_pre
        m = _VERSION_RE.match(self.text)
        if not m:
            raise ValueError("cannot parse version %r" % text)
        self.release = tuple(int(p) for p in m.group("release").split("."))
        word = m.group("pre")
        if word is None:
            self.pre = None
        else:
            rank = _PRE_ORDER.get(word.lower(), -1)
            self.pre = (rank, int(m.group("num") or 0))

    @property
    def is_prerelease(self):
        return self.pre is not None or self.forced_pre

    @property
    def sort_key(self):
        # Pad so 4.6 and 4.6.0 compare equal, and so a release always sorts
        # above any of its own prereleases.
        release = self.release + (0,) * (4 - len(self.release))
        if self.pre is None:
            return (release, 1, (0, 0))
        return (release, 0, self.pre)

    def component(self, index):
        return self.release[index] if index < len(self.release) else 0

    def __eq__(self, other):
        return isinstance(other, Version) and self.sort_key == other.sort_key

    def __lt__(self, other):
        return self.sort_key < other.sort_key

    def __hash__(self):
        return hash(self.sort_key)

    def __str__(self):
        return self.text


class Release:
    """One available version, with its date if the upstream told us one."""

    __slots__ = ("version", "date")

    def __init__(self, version, date=None):
        self.version = version
        self.date = date

    @property
    def age_days(self):
        if self.date is None:
            return None
        return (datetime.now(timezone.utc) - self.date).days


def substitute(template, version):
    """Expand __VERSION__ and friends in a url or filename template."""
    out = template.replace("__VERSION__", version.text)
    out = out.replace("__MAJOR__", str(version.component(0)))
    out = out.replace("__MINOR__", str(version.component(1)))
    out = out.replace("__PATCH__", str(version.component(2)))
    return out


def filename_regex(template):
    """Turn a filename template into a regex matching any version of it."""
    parts = re.split(r"(__VERSION__|__MAJOR__|__MINOR__|__PATCH__)", template)
    out = []
    for part in parts:
        if part == "__VERSION__":
            out.append(r"[0-9][0-9A-Za-z._-]*")
        elif part in ("__MAJOR__", "__MINOR__", "__PATCH__"):
            out.append(r"[0-9]+")
        else:
            out.append(re.escape(part))
    return re.compile("^" + "".join(out) + "$")


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def http_open(url, headers=None):
    """Open a URL, retrying the failures that are worth retrying."""
    hdrs = {"User-Agent": USER_AGENT}
    if headers:
        hdrs.update(headers)
    last = None
    for attempt in range(HTTP_RETRIES):
        req = urllib.request.Request(url, headers=hdrs)
        try:
            return urllib.request.urlopen(req, timeout=HTTP_TIMEOUT)
        except urllib.error.HTTPError as exc:
            # 4xx will not improve by asking again; 5xx might.
            if exc.code < 500:
                raise Fail("HTTP %d %s for %s" % (exc.code, exc.reason, url))
            last = exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last = exc
        if attempt < HTTP_RETRIES - 1:
            time.sleep(2 ** attempt)
    raise Fail("could not fetch %s: %s" % (url, last))


def http_text(url, headers=None):
    with http_open(url, headers) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


# ---------------------------------------------------------------------------
# Version providers
#
# Each returns a list of Release, newest first is not required -- the caller
# sorts. A provider that cannot supply dates leaves them None rather than
# inventing them.
# ---------------------------------------------------------------------------

def _iso_date(text):
    if not text:
        return None
    text = text.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


_DATE_PATTERNS = [
    (re.compile(r"(\d{4}-\d{2}-\d{2})"), "%Y-%m-%d"),
    (re.compile(r"(\d{2}-[A-Za-z]{3}-\d{4})"), "%d-%b-%Y"),
    (re.compile(r"([A-Za-z]{3}\s+\d{1,2}\s+\d{4})"), "%b %d %Y"),
]


# Prose dates as written on a release page: "Aug. 5, 2026", "June 10, 2026".
# The month is abbreviated inconsistently, so only its first three letters are
# used, which is all %b wants anyway.
_PROSE_DATE_RE = re.compile(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2}),\s+(\d{4})\b")


def _loose_date(text):
    """Pull a date out of a directory-listing or release-page line."""
    m = _PROSE_DATE_RE.search(text)
    if m:
        try:
            return datetime.strptime("%s %s %s" % (m.group(1)[:3], m.group(2), m.group(3)),
                                     "%b %d %Y").replace(tzinfo=timezone.utc)
        except ValueError:
            pass  # not a month name after all; fall through to the other forms
    for pattern, fmt in _DATE_PATTERNS:
        m = pattern.search(text)
        if m:
            try:
                return datetime.strptime(m.group(1), fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


def _rfc822_date(text):
    if not text:
        return None
    text = re.sub(r"\bUT$", "+0000", text.strip())
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            dt = datetime.strptime(text, fmt)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def probe_github(spec):
    repo = spec.get("repo")
    if not repo:
        raise Fail("versions: kind github needs a 'repo: owner/name'")
    source = spec.get("source", "releases")
    pattern = re.compile(spec.get("tag_pattern") or r"^v?(?P<version>.+)$")

    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token

    if source == "tags":
        url = "https://api.github.com/repos/%s/tags?per_page=100" % repo
    else:
        url = "https://api.github.com/repos/%s/releases?per_page=100" % repo

    try:
        data = json.loads(http_text(url, headers))
    except Fail as exc:
        if "HTTP 403" in str(exc) and not token:
            raise Fail("%s\nGitHub is rate-limiting anonymous requests. Set "
                       "GITHUB_TOKEN to a personal access token and retry." % exc)
        raise
    if not isinstance(data, list):
        raise Fail("unexpected response from %s" % url)

    out = []
    for item in data:
        if source == "tags":
            tag, date = item.get("name"), None
        else:
            if item.get("draft"):
                continue
            tag = item.get("tag_name")
            date = _iso_date(item.get("published_at") or item.get("created_at"))
        m = pattern.match(tag or "")
        if not m:
            continue
        out.append((m.group("version"), date))
    return out


def probe_git(spec):
    url = spec.get("url")
    if not url:
        raise Fail("versions: kind git needs a 'url' to a git repository")
    if not shutil.which("git"):
        raise Fail("versions: kind git needs the 'git' command in PATH")
    pattern = re.compile(spec.get("tag_pattern") or r"^v?(?P<version>.+)$")
    try:
        proc = subprocess.run(["git", "ls-remote", "--tags", "--refs", url],
                              capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        raise Fail("git ls-remote %s timed out" % url)
    if proc.returncode != 0:
        raise Fail("git ls-remote %s failed:\n%s" % (url, proc.stderr.strip()))

    out = []
    for line in proc.stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        tag = parts[1].rsplit("/", 1)[-1]
        m = pattern.match(tag)
        if m:
            out.append((m.group("version"), None))  # ls-remote carries no dates
    return out


def probe_html_index(spec):
    url = spec.get("url")
    pattern = spec.get("pattern")
    if not url or not pattern:
        raise Fail("versions: kind html_index needs both 'url' and 'pattern'")
    regex = re.compile(pattern)
    body = http_text(url)

    found = {}
    for line in body.splitlines():
        for m in regex.finditer(line):
            version = m.group("version")
            # Listings repeat each name (href and link text); keep the first
            # date seen, and do not let a later dateless match erase it.
            date = _loose_date(line)
            if version not in found or (found[version] is None and date is not None):
                found[version] = date
    return list(found.items())


def probe_sourceforge(spec):
    project = spec.get("project")
    if not project:
        raise Fail("versions: kind sourceforge needs a 'project'")
    pattern = spec.get("pattern")
    if not pattern:
        raise Fail("versions: kind sourceforge needs a 'pattern'")
    regex = re.compile(pattern)
    path = spec.get("path", "/")
    url = "https://sourceforge.net/projects/%s/rss?path=%s" % (project, path)

    body = http_text(url)
    try:
        root = ET.fromstring(body)
    except ET.ParseError as exc:
        raise Fail("could not parse the SourceForge feed at %s: %s" % (url, exc))

    found = {}
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        m = regex.search(title)
        if not m:
            continue
        version = m.group("version")
        date = _rfc822_date(item.findtext("pubDate"))
        if version not in found or (found[version] is None and date is not None):
            found[version] = date
    return list(found.items())


PROBES = {
    "github": probe_github,
    "git": probe_git,
    "html_index": probe_html_index,
    "sourceforge": probe_sourceforge,
}


def probe_versions(spec):
    """Return available Releases for a package, newest first."""
    vspec = spec["versions"]
    kind = vspec.get("kind")
    if kind not in PROBES:
        raise Fail("unknown version source kind %r (known: %s)"
                   % (kind, ", ".join(sorted(PROBES))))
    stable = vspec.get("stable_pattern")
    stable_re = re.compile(stable) if stable else None

    releases = []
    for text, date in PROBES[kind](vspec):
        try:
            version = Version(text, forced_pre=bool(stable_re and not stable_re.match(text)))
        except ValueError:
            continue  # an upstream name we do not understand is not a version
        releases.append(Release(version, date))

    if not releases:
        raise Fail("no versions matched at the upstream for this package.\n"
                   "The pattern in packages.yaml may no longer fit what upstream publishes.")
    releases.sort(key=lambda r: r.version.sort_key, reverse=True)
    return releases


# ---------------------------------------------------------------------------
# Download, with a progress bar
# ---------------------------------------------------------------------------

def human_bytes(n):
    if n is None:
        return "?"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return "%.0f %s" % (n, unit) if unit == "B" else "%.1f %s" % (n, unit)
        n /= 1024.0


def human_time(seconds):
    if seconds is None or seconds != seconds or seconds < 0 or seconds > 359999:
        return "--:--"
    return "%02d:%02d" % (int(seconds) // 60, int(seconds) % 60)


class Progress:
    """A one-line progress bar on a terminal, periodic lines when piped."""

    WIDTH = 30

    def __init__(self, total, label, stream=None):
        self.total = total if total and total > 0 else None
        self.label = label
        self.stream = stream if stream is not None else sys.stderr
        self.tty = hasattr(self.stream, "isatty") and self.stream.isatty()
        self.done = 0
        self.start = time.time()
        self.last_draw = 0.0
        self.closed = False

    def update(self, count):
        self.done += count
        now = time.time()
        # Redraw at most ~20x/sec on a terminal; once every 5s when piped, so
        # a build log gets progress without getting a wall of it.
        interval = 0.05 if self.tty else 5.0
        if now - self.last_draw >= interval:
            self.last_draw = now
            self._draw(now)

    def _draw(self, now):
        elapsed = max(now - self.start, 1e-6)
        rate = self.done / elapsed
        if self.total:
            frac = min(self.done / self.total, 1.0)
            filled = int(self.WIDTH * frac)
            bar = "#" * filled + "-" * (self.WIDTH - filled)
            eta = (self.total - self.done) / rate if rate > 0 else None
            line = "  [%s] %3.0f%%  %s / %s  %s/s  eta %s" % (
                bar, frac * 100, human_bytes(self.done), human_bytes(self.total),
                human_bytes(rate), human_time(eta))
        else:
            line = "  %s downloaded  %s/s" % (human_bytes(self.done), human_bytes(rate))
        if self.tty:
            self.stream.write("\r\033[K" + line)
        else:
            self.stream.write(line + "\n")
        self.stream.flush()

    def close(self):
        if self.closed:
            return
        self.closed = True
        self._draw(time.time())
        if self.tty:
            self.stream.write("\n")
        self.stream.flush()


def download(url, dest_dir, name, quiet=False):
    """Download to a temp file beside the destination, hashing as it goes.

    Returns (temp_path, sha256). The caller moves it into place once it is
    satisfied; nothing partial ever lands under the real name.
    """
    os.makedirs(dest_dir, exist_ok=True)
    digest = hashlib.sha256()
    fd, tmp = tempfile.mkstemp(prefix="." + name + ".", dir=dest_dir)
    progress = None
    try:
        with http_open(url) as resp, os.fdopen(fd, "wb") as out:
            length = resp.headers.get("Content-Length")
            total = int(length) if length and length.isdigit() else None
            if not quiet:
                progress = Progress(total, name)
            while True:
                chunk = resp.read(262144)
                if not chunk:
                    break
                out.write(chunk)
                digest.update(chunk)
                if progress:
                    progress.update(len(chunk))
        if progress:
            progress.close()
        # mkstemp gives 0600; sources should be readable like any other file.
        os.chmod(tmp, 0o644)
        return tmp, digest.hexdigest()
    except BaseException:
        if progress:
            progress.close()
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ---------------------------------------------------------------------------
# Editing the tree
# ---------------------------------------------------------------------------

def write_atomic(path, text):
    directory = os.path.dirname(os.path.abspath(path)) or "."
    fd, tmp = tempfile.mkstemp(prefix="." + os.path.basename(path) + ".", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        if os.path.exists(path):
            shutil.copymode(path, tmp)
        else:
            os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def makefile_current_version(text, var):
    m = re.search(r"^[ \t]*%s[ \t]*:?=[ \t]*(\S+)[ \t]*$" % re.escape(var),
                  text, re.MULTILINE)
    return m.group(1) if m else None


def makefile_set_version(text, var, version, path="Makefile"):
    """Rewrite one variable assignment, preserving its original spacing."""
    pattern = re.compile(r"^([ \t]*%s[ \t]*:?=[ \t]*)(\S+)([ \t]*)$" % re.escape(var),
                         re.MULTILINE)
    matches = pattern.findall(text)
    if not matches:
        raise Fail("%s: no assignment to '%s' found.\n"
                   "Check 'version_var' for this package in %s." % (path, var, CONFIG_NAME))
    if len(matches) > 1:
        raise Fail("%s: '%s' is assigned %d times; refusing to guess which one "
                   "pins the version." % (path, var, len(matches)))
    return pattern.sub(lambda m: m.group(1) + version + m.group(3), text, count=1)


class Manifest:
    """sources/manifest.txt: '<filename>  <sha256>  <url>', plus comments."""

    ENTRY = re.compile(r"^(\S+)\s+([0-9a-f]{64})\s+(\S+)\s*$")

    def __init__(self, path):
        self.path = path
        with open(path, "r", encoding="utf-8") as fh:
            self.lines = fh.read().splitlines()

    def find(self, name_regex):
        """Index of the entry line whose filename matches, or None."""
        for i, line in enumerate(self.lines):
            m = self.ENTRY.match(line)
            if m and name_regex.match(m.group(1)):
                return i
        return None

    def entry(self, index):
        m = self.ENTRY.match(self.lines[index])
        if not m:
            raise Fail("%s:%d is not a manifest entry" % (self.path, index + 1))
        return (m.group(1), m.group(2), m.group(3))

    def _name_width(self):
        """Reuse the column width the file already uses, so diffs stay small."""
        widths = [m.start(2) for m in
                  (self.ENTRY.match(line) for line in self.lines) if m]
        return max(widths) if widths else 32

    def format(self, name, sha, url):
        width = max(self._name_width(), len(name) + 1)
        return "%-*s%s  %s" % (width, name, sha, url)

    def set(self, index, name, sha, url):
        if index is None:
            self.lines.append(self.format(name, sha, url))
        else:
            self.lines[index] = self.format(name, sha, url)

    def last_entry_index(self):
        last = None
        for i, line in enumerate(self.lines):
            if self.ENTRY.match(line):
                last = i
        return last

    def insert_after_entries(self, name, sha, url):
        last = self.last_entry_index()
        line = self.format(name, sha, url)
        if last is None:
            self.lines.append(line)
        else:
            self.lines.insert(last + 1, line)

    def text(self):
        return "\n".join(self.lines) + "\n"


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def resolve_paths(config, spec):
    return {
        "makefile": os.path.join(REPO_ROOT, spec["makefile"]),
        "manifest": os.path.join(REPO_ROOT, config["manifest"]),
        "sources": os.path.join(REPO_ROOT, config["sources_dir"]),
    }


def current_version(spec, paths):
    if not os.path.exists(paths["makefile"]):
        raise Fail("%s does not exist" % spec["makefile"])
    with open(paths["makefile"], "r", encoding="utf-8") as fh:
        return makefile_current_version(fh.read(), spec["version_var"])


def cmd_list_packages(config):
    print("packages described in %s:\n" % CONFIG_NAME)
    width = max(len(n) for n in config["packages"])
    for name in sorted(config["packages"]):
        spec = config["packages"][name]
        paths = resolve_paths(config, spec)
        try:
            have = current_version(spec, paths) or "?"
        except Fail:
            have = "?"
        print("  %-*s  %-10s  %s  (%s)" % (width, name, have, spec["makefile"],
                                           spec["versions"].get("kind", "?")))
    return 0


def cmd_list_versions(config, name, spec, args):
    paths = resolve_paths(config, spec)
    have = current_version(spec, paths)
    releases = probe_versions(spec)
    if not args.include_prerelease:
        releases = [r for r in releases if not r.version.is_prerelease]
        if not releases:
            raise Fail("every version upstream is a prerelease; "
                       "pass --include-prerelease to see them")
    shown = releases[:args.limit] if args.limit else releases

    if args.json:
        print(json.dumps({
            "package": name,
            "current": have,
            "versions": [{
                "version": r.version.text,
                "date": r.date.date().isoformat() if r.date else None,
                "age_days": r.age_days,
                "prerelease": r.version.is_prerelease,
            } for r in shown],
        }, indent=2))
        return 0

    print("%s -- currently pinned at %s (%s)\n" % (name, have or "?", spec["makefile"]))
    print("  %-16s %-12s %-9s %s" % ("VERSION", "DATE", "AGE", ""))
    for r in shown:
        marker = "<- current" if have and r.version == Version(have) else ""
        if r.version.is_prerelease and marker:
            marker += " (prerelease)"
        elif r.version.is_prerelease:
            marker = "prerelease"
        date = r.date.date().isoformat() if r.date else "-"
        age = "%d days" % r.age_days if r.age_days is not None else "-"
        print("  %-16s %-12s %-9s %s" % (r.version, date, age, marker))
    if args.limit and len(releases) > len(shown):
        print("\n  ... %d more, use --limit 0 to see all" % (len(releases) - len(shown)))
    return 0


def cmd_update(config, name, spec, args):
    paths = resolve_paths(config, spec)
    have_text = current_version(spec, paths)

    if args.version:
        try:
            target = Version(args.version)
        except ValueError:
            raise Fail("cannot parse --version %r" % args.version)
        note = "requested"
    else:
        releases = probe_versions(spec)
        if not args.include_prerelease:
            releases = [r for r in releases if not r.version.is_prerelease]
            if not releases:
                raise Fail("the only versions upstream are prereleases; pass "
                           "--include-prerelease to use one, or give --version")
        target = releases[0].version
        note = "latest upstream"

    url = substitute(spec["url"], target)
    filename = substitute(spec["filename"], target)
    dest = os.path.join(paths["sources"], filename)

    print("package   %s" % name)
    print("current   %s" % (have_text or "?"))
    print("target    %s  (%s)" % (target, note))
    print("tarball   %s" % os.path.relpath(dest, REPO_ROOT))
    print("url       %s" % url)

    if have_text and Version(have_text) == target and os.path.exists(dest) and not args.force:
        print("\nAlready at %s and the tarball is present. Nothing to do." % target)
        print("(Use --force to re-download and re-checksum it.)")
        return 0

    if args.dry_run:
        print("\ndry run: would download the tarball, then update")
        print("  %s: %s = %s" % (spec["makefile"], spec["version_var"], target))
        print("  %s: entry for %s" % (config["manifest"], filename))
        return 0

    # 1. Get the bytes and their checksum before touching anything tracked.
    if os.path.exists(dest) and not args.force:
        print("\nusing the tarball already in %s" % config["sources_dir"])
        sha = sha256_of(dest)
        staged = None
    else:
        print()
        try:
            staged, sha = download(url, paths["sources"], filename, quiet=args.quiet)
        except Fail as exc:
            if "HTTP 404" in str(exc):
                raise Fail("%s\nUpstream has no such file. Either %s is not a real version,\n"
                           "or the url template for '%s' in %s needs updating.\n"
                           "Run with --list-versions to see what is available."
                           % (exc, target, name, CONFIG_NAME))
            raise
    print("sha256    %s" % sha)

    # 2. Prepare both edits in memory, so a failure in either writes neither.
    manifest = Manifest(paths["manifest"])
    name_re = filename_regex(spec["filename"])
    index = manifest.find(name_re)
    old_entry = manifest.entry(index) if index is not None else None

    if old_entry and old_entry[0] == filename and old_entry[1] != sha:
        raise Fail("%s already lists %s with a different checksum.\n"
                   "  manifest %s\n  download %s\n"
                   "The upstream file may have been re-rolled, or this download may be\n"
                   "corrupt. Do not update the manifest without confirming why."
                   % (config["manifest"], filename, old_entry[1], sha))

    if index is None:
        manifest.insert_after_entries(filename, sha, url)
    else:
        manifest.set(index, filename, sha, url)

    with open(paths["makefile"], "r", encoding="utf-8") as fh:
        makefile_text = fh.read()
    new_makefile = makefile_set_version(makefile_text, spec["version_var"],
                                        target.text, spec["makefile"])

    # 3. Commit: tarball into place, then the two text files.
    if staged:
        os.replace(staged, dest)
    write_atomic(paths["manifest"], manifest.text())
    write_atomic(paths["makefile"], new_makefile)

    print("\nupdated:")
    print("  %-28s %s = %s" % (spec["makefile"] + ":", spec["version_var"], target))
    if old_entry:
        print("  %-28s %s" % (config["manifest"] + ":", old_entry[0]))
        print("  %-28s   -> %s" % ("", filename))
    else:
        print("  %-28s + %s" % (config["manifest"] + ":", filename))
    if staged:
        print("  %-28s %s" % (config["sources_dir"] + ":", filename))

    if old_entry and old_entry[0] != filename:
        old_path = os.path.join(paths["sources"], old_entry[0])
        if os.path.exists(old_path):
            if args.keep_old:
                print("\nThe previous tarball is still in %s:\n  %s"
                      % (config["sources_dir"], old_entry[0]))
            else:
                os.unlink(old_path)
                print("\nremoved the superseded tarball %s" % old_entry[0])

    print("\nReview with 'git diff', then build with:\n  make -f %s clean && make -f %s"
          % (spec["makefile"], spec["makefile"]))
    return 0


# ---------------------------------------------------------------------------
# Self test
# ---------------------------------------------------------------------------

def self_test():
    failures = []

    def check(label, got, want):
        if got != want:
            failures.append("%s\n    got  %r\n    want %r" % (label, got, want))

    # Version ordering, including the shapes these upstreams actually publish.
    order = ["1.2.3", "1.10.0", "20.1.0"]
    check("numeric ordering, not lexical",
          [str(v) for v in sorted(Version(t) for t in reversed(order))], order)
    check("release beats its own rc", Version("1.12.0") > Version("1.12.0-rc1"), True)
    check("rc ordering", Version("1.12.0-rc2") > Version("1.12.0-rc1"), True)
    check("padding: 4.6 == 4.6.0", Version("4.6") == Version("4.6.0"), True)
    check("rc is a prerelease", Version("20.1.0-rc1").is_prerelease, True)
    check("plain is not", Version("20.1.0").is_prerelease, False)
    check("stable_pattern forces prerelease",
          Version("5.45.1", forced_pre=True).is_prerelease, True)
    try:
        Version("not-a-version")
        failures.append("Version accepted garbage")
    except ValueError:
        pass

    # Templates.
    check("substitute", substitute("R-__VERSION__ in R-__MAJOR__", Version("4.4.1")),
          "R-4.4.1 in R-4")
    check("filename_regex matches other versions",
          bool(filename_regex("julia-__VERSION__-full.tar.gz").match("julia-1.9.0-full.tar.gz")),
          True)
    check("filename_regex is anchored",
          bool(filename_regex("R-__VERSION__.tar.xz").match("XR-4.4.1.tar.xz")), False)

    # Makefile rewriting preserves the tab alignment these files use.
    src = "include config/base.config\n\nOBLASVER\t\t= 0.3.30\nOBLAS\t= OpenBLAS-${OBLASVER}\n"
    check("makefile_current_version", makefile_current_version(src, "OBLASVER"), "0.3.30")
    check("makefile_set_version keeps alignment",
          makefile_set_version(src, "OBLASVER", "0.3.31"),
          "include config/base.config\n\nOBLASVER\t\t= 0.3.31\nOBLAS\t= OpenBLAS-${OBLASVER}\n")
    check("derived variables are left alone",
          "OBLAS\t= OpenBLAS-${OBLASVER}" in makefile_set_version(src, "OBLASVER", "0.3.31"),
          True)
    try:
        makefile_set_version(src, "NOSUCHVAR", "1.0")
        failures.append("makefile_set_version accepted a missing variable")
    except Fail:
        pass
    try:
        makefile_set_version("A = 1\nA = 2\n", "A", "3")
        failures.append("makefile_set_version accepted a doubly-assigned variable")
    except Fail:
        pass

    # The config parser, on the shapes packages.yaml uses.
    parsed = parse_simple_yaml(
        '# comment\n'
        'defaults:\n'
        '  sources_dir: sources\n'
        'packages:\n'
        '  julia:\n'
        '    makefile: Makefile.julia   # trailing comment\n'
        '    url: "https://x/__VERSION__#frag"\n'
        '    versions:\n'
        '      kind: github\n'
        '      tag_pattern: "^v(?P<version>[0-9]+)$"\n'
    )
    check("nested mappings", parsed["packages"]["julia"]["versions"]["kind"], "github")
    check("trailing comment stripped", parsed["packages"]["julia"]["makefile"], "Makefile.julia")
    check("'#' inside a quoted value survives",
          parsed["packages"]["julia"]["url"], "https://x/__VERSION__#frag")
    check("escapes in a quoted regex survive",
          parsed["packages"]["julia"]["versions"]["tag_pattern"], "^v(?P<version>[0-9]+)$")
    for bad, why in [("- a\n", "sequence"), ("a: {b: c}\n", "flow mapping"), ("junk\n", "no colon")]:
        try:
            parse_simple_yaml(bad)
            failures.append("parser accepted a %s" % why)
        except Fail:
            pass

    # Date scraping.
    check("apache listing date",
          _loose_date('<a href="octave-10.3.0.tar.xz">octave-10.3.0.tar.xz</a>  2025-06-01 10:00  30M'),
          datetime(2025, 6, 1, tzinfo=timezone.utc))
    check("release-page prose date, abbreviated month",
          _loose_date("Python 3.14.7 - Aug. 5, 2026"),
          datetime(2026, 8, 5, tzinfo=timezone.utc))
    check("release-page prose date, spelled-out month",
          _loose_date("Python 3.14.4 - April 7, 2026"),
          datetime(2026, 4, 7, tzinfo=timezone.utc))
    # A prerelease must not match as a prefix of a real version.
    py_pat = re.compile("Python (?P<version>3\\.[0-9]+\\.[0-9]+) - ")
    py_hit = py_pat.search("Python 3.14.7 - Aug. 5, 2026")
    check("release page: final version matches",
          py_hit.group("version") if py_hit else None, "3.14.7")
    check("release page: rc does not match",
          py_pat.search("Python 3.15.0rc1 - Aug. 4, 2026"), None)
    check("sourceforge pubDate",
          _rfc822_date("Tue, 04 Aug 2026 20:36:56 UT"),
          datetime(2026, 8, 4, 20, 36, 56, tzinfo=timezone.utc))
    check("github timestamp", _iso_date("2025-06-01T10:00:00Z"),
          datetime(2025, 6, 1, 10, 0, tzinfo=timezone.utc))
    check("age in days",
          Release(Version("1.0"), datetime.now(timezone.utc) - timedelta(days=7)).age_days, 7)

    # Manifest rewriting, against the real file's layout.
    fd, tmp = tempfile.mkstemp()
    try:
        with os.fdopen(fd, "w") as fh:
            fh.write("# header\n\n"
                     "OpenBLAS-0.3.30.tar.gz          %s  https://example/a\n"
                     "Python-3.14.3.tar.xz            %s  https://example/b\n"
                     "\n# trailer\n" % ("a" * 64, "b" * 64))
        man = Manifest(tmp)
        idx = man.find(filename_regex("OpenBLAS-__VERSION__.tar.gz"))
        check("manifest find", idx, 2)
        check("manifest entry", man.entry(idx)[0], "OpenBLAS-0.3.30.tar.gz")
        man.set(idx, "OpenBLAS-0.3.31.tar.gz", "c" * 64, "https://example/c")
        out = man.text().splitlines()
        check("manifest rewrite", out[2],
              "OpenBLAS-0.3.31.tar.gz".ljust(32) + "c" * 64 + "  https://example/c")
        check("other entries untouched", out[3].split()[0], "Python-3.14.3.tar.xz")
        check("comments untouched", (out[0], out[5]), ("# header", "# trailer"))
        check("no entry for an unknown package",
              man.find(filename_regex("nosuch-__VERSION__.tar.gz")), None)
    finally:
        os.unlink(tmp)

    # Every package in the real packages.yaml must be internally consistent:
    # its Makefile must exist and its pinned version must produce the exact
    # filename and url the manifest already records.
    config = load_config(os.path.join(REPO_ROOT, CONFIG_NAME))
    manifest = Manifest(os.path.join(REPO_ROOT, config["manifest"]))
    for name, spec in sorted(config["packages"].items()):
        paths = resolve_paths(config, spec)
        if not os.path.exists(paths["makefile"]):
            failures.append("%s: %s does not exist" % (name, spec["makefile"]))
            continue
        have = current_version(spec, paths)
        if not have:
            failures.append("%s: no '%s' assignment in %s"
                            % (name, spec["version_var"], spec["makefile"]))
            continue
        version = Version(have)
        idx = manifest.find(filename_regex(spec["filename"]))
        if idx is None:
            failures.append("%s: no manifest entry matches %s" % (name, spec["filename"]))
            continue
        entry_name, _, entry_url = manifest.entry(idx)
        check("%s: filename for %s" % (name, have), substitute(spec["filename"], version), entry_name)
        check("%s: url for %s" % (name, have), substitute(spec["url"], version), entry_url)
        if spec["versions"].get("kind") not in PROBES:
            failures.append("%s: unknown version kind %r" % (name, spec["versions"].get("kind")))

    if failures:
        print("self-test: %d FAILURES\n" % len(failures))
        for f in failures:
            print("  " + f)
        return 1
    print("self-test: all checks passed")
    return 0


# ---------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        prog="update-package.py",
        description="Download a package version and point the build at it.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  update-package.py --list-packages
  update-package.py --package julia --list-versions
  update-package.py --package julia
  update-package.py --package julia --version 1.11.7
  update-package.py --package llvm --dry-run
""")
    p.add_argument("--package", "-p", metavar="NAME",
                   help="package to operate on, as named in " + CONFIG_NAME)
    p.add_argument("--version", "-V", metavar="VERSION",
                   help="version to use (default: the latest found upstream)")
    p.add_argument("--list-versions", "-l", action="store_true",
                   help="list available versions with their dates and ages")
    p.add_argument("--list-packages", action="store_true",
                   help="list the packages this tool knows about")
    p.add_argument("--include-prerelease", action="store_true",
                   help="do not hide release candidates and development versions")
    p.add_argument("--limit", "-n", type=int, default=15, metavar="N",
                   help="with --list-versions, show N entries (0 for all; default 15)")
    p.add_argument("--dry-run", "-N", action="store_true",
                   help="report what would change without downloading or writing")
    p.add_argument("--force", "-f", action="store_true",
                   help="re-download even if the tarball is already present")
    p.add_argument("--keep-old", action="store_true",
                   help="keep the superseded tarball in sources/")
    p.add_argument("--quiet", "-q", action="store_true",
                   help="no progress bar")
    p.add_argument("--json", action="store_true",
                   help="with --list-versions, emit JSON")
    p.add_argument("--config", metavar="PATH",
                   default=os.path.join(REPO_ROOT, CONFIG_NAME),
                   help="path to " + CONFIG_NAME)
    p.add_argument("--self-test", action="store_true",
                   help="run the built-in checks and exit")
    return p


def main(argv):
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    if not os.path.exists(args.config):
        raise Fail("no %s found (looked in %s)" % (CONFIG_NAME, args.config))
    config = load_config(args.config)

    if args.list_packages:
        return cmd_list_packages(config)

    if not args.package:
        parser.print_usage(sys.stderr)
        raise Fail("give --package NAME (or --list-packages to see the choices)")

    packages = config["packages"]
    name = args.package
    if name not in packages:
        # Be forgiving about case, since the Makefiles are not consistent.
        matches = [k for k in packages if k.lower() == name.lower()]
        if not matches:
            raise Fail("unknown package %r.\nKnown packages: %s"
                       % (name, ", ".join(sorted(packages))))
        name = matches[0]
    spec = packages[name]

    if args.list_versions:
        return cmd_list_versions(config, name, spec, args)
    return cmd_update(config, name, spec, args)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Fail as exc:
        print("update-package.py: %s" % exc, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        sys.exit(130)
