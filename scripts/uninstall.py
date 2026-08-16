#!/usr/bin/env python3
"""Remove an installed package from the nlytiq tree.

    uninstall.py --package octave              # dry run: what would go
    uninstall.py --package octave --yes        # actually remove it
    uninstall.py --all --yes                   # every package it knows about
    uninstall.py --orphans                     # files no package claims

Every package in this tree installs with 'make install' into one shared
prefix, and nothing records what went where. So removing a package means
working out afterwards which of the prefix's files belong to it. Ownership
comes from four sources, strongest first:

    packlist        perl's own .packlist files, which list exactly what each
                    distribution installed, bin/ scripts included
    python_record   pip's <dist>.dist-info/RECORD, likewise exact
    owns            the globs declared in uninstall.yaml
    shebang         a bin/ script whose interpreter is this tree's perl or
                    python belongs to that package

A stronger source always wins, so a file pip recorded is never re-claimed by
a glob -- which is what keeps bin/cmake, installed by the cmake wheel, from
being mistaken for part of llvm.

Nothing is deleted without --yes. A file claimed by two packages is never
deleted while removing just one of them.

Standard library only, like the rest of the tooling here.
"""

import argparse
import glob as globmod
import importlib.util
import json
import os
import re
import shutil
import stat
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_NAME = "uninstall.yaml"

# Claim strength. Lower is stronger; a stronger claim is never overridden.
TIER_RECORDED = 0     # perl .packlist, pip RECORD
TIER_DECLARED = 1     # 'owns' globs in uninstall.yaml
TIER_INFERRED = 2     # shebang scan

TIER_NAMES = {TIER_RECORDED: "recorded", TIER_DECLARED: "declared",
              TIER_INFERRED: "shebang"}

# Prefixes that must never be handed to a recursive delete, whatever the
# config says. Checked against the resolved path.
FORBIDDEN_PREFIXES = {
    "/", "/usr", "/usr/local", "/usr/bin", "/usr/lib", "/usr/share",
    "/opt", "/bin", "/sbin", "/lib", "/lib64", "/etc", "/var", "/tmp",
    "/home", "/root", "/boot", "/dev", "/proc", "/sys", "/Applications",
    "/Library", "/System",
}


class Fail(Exception):
    """A fatal, already-explained error."""


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_yaml_parser():
    """Reuse the YAML subset parser that update-package.py already carries."""
    path = os.path.join(REPO_ROOT, "scripts", "update-package.py")
    if not os.path.exists(path):
        raise Fail("cannot find scripts/update-package.py, whose YAML parser "
                   "this shares")
    spec = importlib.util.spec_from_file_location("update_package", path)
    if spec is None or spec.loader is None:
        raise Fail("cannot load scripts/update-package.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_config(path, parser_module):
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    try:
        import yaml  # noqa: F401
    except ImportError:
        data = parser_module.parse_simple_yaml(text, path)
    else:
        data = yaml.safe_load(text)
    if not isinstance(data, dict) or not data.get("packages"):
        raise Fail("%s: no 'packages:' mapping found" % path)
    return data


def resolve_prefix(explicit, config):
    """Work out NLYTIQ_INST_PATH, the same way the Makefiles compute it."""
    if explicit:
        return os.path.abspath(os.path.expanduser(explicit))

    defaults = config.get("defaults") or {}
    rel = defaults.get("prefix_from", "config/base.config")
    base = os.path.join(REPO_ROOT, rel)
    if not os.path.exists(base):
        raise Fail("cannot read %s to find the install prefix; pass --prefix"
                   % rel)

    values = {}
    with open(base, "r", encoding="utf-8") as fh:
        for line in fh:
            m = re.match(r"^\s*([A-Z_]+)\s*:?=\s*(.*?)\s*$", line)
            if m and not line.lstrip().startswith("#"):
                values[m.group(1)] = m.group(2)

    def expand(text, depth=0):
        if depth > 8:
            return text
        def sub(m):
            name = m.group(1)
            if name == "HOME":
                return os.path.expanduser("~")
            return expand(values.get(name, ""), depth + 1)
        return re.sub(r"\$[{(]([A-Za-z_]+)[})]", sub, text)

    for key in ("NLYTIQ_INST_PATH", "NLYTIQ_TOP"):
        if key in values:
            path = expand(values[key]).strip()
            if path:
                return os.path.abspath(os.path.expanduser(path))
    raise Fail("no NLYTIQ_INST_PATH or NLYTIQ_TOP in %s; pass --prefix" % rel)


def validate_prefix(prefix):
    """Refuse to operate on anything that is not plainly an install tree."""
    real = os.path.realpath(prefix)
    if not os.path.isabs(real):
        raise Fail("prefix must be an absolute path: %s" % prefix)
    if real.rstrip("/") in FORBIDDEN_PREFIXES or real == "/":
        raise Fail("refusing to operate on %s -- that is a system directory,\n"
                   "not an nlytiq install prefix." % real)
    if real == os.path.realpath(os.path.expanduser("~")):
        raise Fail("refusing to operate on your home directory (%s)." % real)
    if len([p for p in real.split(os.sep) if p]) < 2:
        raise Fail("refusing to operate on %s -- too close to the root of the\n"
                   "filesystem to be an install prefix." % real)
    if not os.path.isdir(real):
        raise Fail("prefix does not exist or is not a directory: %s" % real)
    if os.path.realpath(REPO_ROOT).startswith(real + os.sep):
        raise Fail("the prefix %s contains this git repository.\n"
                   "Refusing to remove files that would take the source tree "
                   "with them." % real)
    return real


def inside(prefix, path):
    """True when path lies within prefix, without following a final symlink.

    The parent directory is resolved, so a symlinked parent cannot smuggle a
    path outside the prefix, but a symlink at the end is treated as the link
    itself -- we unlink those rather than chasing what they point at.
    """
    parent = os.path.realpath(os.path.dirname(path))
    full = os.path.join(parent, os.path.basename(path))
    return full == prefix or full.startswith(prefix + os.sep)


# ---------------------------------------------------------------------------
# Building the claim map
# ---------------------------------------------------------------------------

class Claims:
    """Which package owns which path, and how confidently."""

    def __init__(self, prefix):
        self.prefix = prefix
        self.files = {}     # relpath -> [tier, {pkg, ...}]
        self.dirs = {}      # reldir  -> [tier, {pkg, ...}]
        # Prefixes other than ours that recorded files claim to live under,
        # learned from .packlist entries. A tree that has been copied or moved
        # still has perl's absolute paths, and its scripts still carry
        # shebangs, pointing at wherever it was installed.
        self.recorded_prefixes = set()

    def _add(self, table, rel, pkg, tier):
        rel = rel.strip("/")
        if not rel:
            return
        cur = table.get(rel)
        if cur is None:
            table[rel] = [tier, {pkg}]
        elif tier < cur[0]:
            table[rel] = [tier, {pkg}]
        elif tier == cur[0]:
            cur[1].add(pkg)
        # a weaker claim on an already-claimed path is simply dropped

    def add_path(self, abspath, pkg, tier):
        if not inside(self.prefix, abspath):
            return
        rel = os.path.relpath(abspath, self.prefix)
        if rel.startswith(".."):
            return
        if os.path.isdir(abspath) and not os.path.islink(abspath):
            self._add(self.dirs, rel, pkg, tier)
        else:
            self._add(self.files, rel, pkg, tier)

    def owners(self, rel):
        """(tier, packages) for a path, using the deepest claim that covers it."""
        hit = self.files.get(rel)
        if hit is not None:
            return hit
        parts = rel.split("/")
        for i in range(len(parts) - 1, 0, -1):
            hit = self.dirs.get("/".join(parts[:i]))
            if hit is not None:
                return hit
        return None


def claim_globs(claims, pkg, patterns):
    for pattern in patterns or []:
        for match in globmod.glob(os.path.join(claims.prefix, pattern)):
            claims.add_path(match, pkg, TIER_DECLARED)


def reroot(path, prefix, learned=None):
    """Map an absolute path recorded under another prefix onto this one.

    perl writes .packlist entries as absolute paths -- /home/joe/local/bin/cpan
    -- fixed at the time perl was installed. Point --prefix at a copy or a
    moved tree and every one of those falls outside it and is silently dropped,
    so attribution quietly changes: perl5 went from 3236 files to 10190 and
    perl5mods from 12819 to 3712 when the same tree was read through a copy,
    because the globs took over from the exact records.

    The recorded prefix is recoverable, because every entry shares it and the
    tail is the same relative path it has here. Find the longest tail of the
    entry that exists under our prefix and use that.
    """
    if inside(prefix, path):
        return path
    parts = [p for p in path.split(os.sep) if p]
    # Try successively shorter tails: bin/cpan, then cpan, and so on.
    for i in range(len(parts)):
        candidate = os.path.join(prefix, *parts[i:])
        if os.path.lexists(candidate):
            if learned is not None and i:
                # Remember where these records think they live, so shebangs
                # written against the same prefix can be recognised too.
                learned.add(os.sep + os.path.join(*parts[:i]))
            return candidate
    return path


def claim_perl_packlists(claims, pkg, want_site):
    """Read perl's own record of what each distribution installed."""
    root = os.path.join(claims.prefix, "lib", "perl5")
    if not os.path.isdir(root):
        return
    for dirpath, _, filenames in os.walk(root):
        if ".packlist" not in filenames:
            continue
        is_site = "site_perl" in dirpath
        if is_site != want_site:
            continue
        try:
            with open(os.path.join(dirpath, ".packlist"), "r",
                      encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    entry = line.strip().split(" ")[0]
                    if entry:
                        claims.add_path(
                            reroot(entry, claims.prefix,
                                   claims.recorded_prefixes),
                            pkg, TIER_RECORDED)
        except OSError:
            continue


def claim_python_records(claims, pkg):
    """Read pip's record of what each wheel installed."""
    pattern = os.path.join(claims.prefix, "lib", "python3.*",
                           "site-packages", "*.dist-info", "RECORD")
    for record in globmod.glob(pattern):
        site = os.path.dirname(os.path.dirname(record))
        try:
            with open(record, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    name = line.split(",")[0].strip()
                    if name:
                        claims.add_path(os.path.normpath(
                            os.path.join(site, name)), pkg, TIER_RECORDED)
        except OSError:
            continue
        claims.add_path(os.path.dirname(record), pkg, TIER_RECORDED)


def claim_shebangs(claims, pkg, interpreter):
    """Attribute bin/ scripts by the interpreter they name."""
    bindir = os.path.join(claims.prefix, "bin")
    if not os.path.isdir(bindir):
        return
    # Accept this tree's interpreter, and the same interpreter under any
    # prefix the recorded files were written against -- a copied or moved
    # tree still carries the original path in both places.
    needles = [os.path.join(claims.prefix, "bin", interpreter)]
    needles += [os.path.join(p, "bin", interpreter)
                for p in claims.recorded_prefixes]
    for name in os.listdir(bindir):
        path = os.path.join(bindir, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "rb") as fh:
                first = fh.readline(200)
        except OSError:
            continue
        if not first.startswith(b"#!"):
            continue
        line = first.decode("utf-8", errors="replace")
        # match both '#!/prefix/bin/perl' and '#!/usr/bin/env perl'
        if (any(n in line for n in needles)
                or re.search(r"\benv\s+%s\b" % re.escape(interpreter), line)):
            claims.add_path(path, pkg, TIER_INFERRED)


CLAIM_SOURCES = {
    "packlist_core": lambda c, p: claim_perl_packlists(c, p, want_site=False),
    "packlist_site": lambda c, p: claim_perl_packlists(c, p, want_site=True),
    "python_record": claim_python_records,
    "shebang_perl": lambda c, p: claim_shebangs(c, p, "perl"),
    "shebang_python": lambda c, p: claim_shebangs(c, p, "python3"),
}


def claim_manpages(claims):
    """Give man/manN/foo.N to whoever owns bin/foo.

    Section 1 pages are named after the program they document, so this
    attributes them without every package having to list its own man pages,
    and without guessing. Pages with no matching binary stay unclaimed.
    """
    for section in sorted(globmod.glob(os.path.join(claims.prefix, "man", "man*")) +
                          globmod.glob(os.path.join(claims.prefix, "share", "man", "man*"))):
        if not os.path.isdir(section):
            continue
        for name in os.listdir(section):
            path = os.path.join(section, name)
            rel = os.path.relpath(path, claims.prefix)
            if claims.owners(rel):
                continue
            stem = re.sub(r"\.\d[A-Za-z]*(\.gz)?$", "", name)
            owner = claims.owners(os.path.join("bin", stem))
            if owner and len(owner[1]) == 1:
                claims.add_path(path, next(iter(owner[1])), TIER_INFERRED)


def build_claims(prefix, packages):
    claims = Claims(prefix)
    # Recorded sources first, then globs, then shebangs, so that the strength
    # ordering holds regardless of the order packages appear in the file.
    for pkg, spec in packages.items():
        for source in spec.get("claims") or []:
            if source not in CLAIM_SOURCES:
                raise Fail("%s: unknown claim source %r for package '%s'"
                           % (CONFIG_NAME, source, pkg))
            if source.startswith(("packlist", "python_record")):
                CLAIM_SOURCES[source](claims, pkg)
    for pkg, spec in packages.items():
        claim_globs(claims, pkg, spec.get("owns"))
    for pkg, spec in packages.items():
        for source in spec.get("claims") or []:
            if source.startswith("shebang"):
                CLAIM_SOURCES[source](claims, pkg)
    claim_manpages(claims)
    return claims


# ---------------------------------------------------------------------------
# Working out what to remove
# ---------------------------------------------------------------------------

def walk_prefix(prefix):
    """Every file and symlink under the prefix, as relative paths."""
    out = []
    for dirpath, dirnames, filenames in os.walk(prefix):
        # do not descend into symlinked directories; they are removed as links
        dirnames[:] = [d for d in dirnames
                       if not os.path.islink(os.path.join(dirpath, d))]
        for name in filenames + [d for d in os.listdir(dirpath)
                                 if os.path.islink(os.path.join(dirpath, d))]:
            path = os.path.join(dirpath, name)
            if os.path.isdir(path) and not os.path.islink(path):
                continue
            out.append(os.path.relpath(path, prefix))
    return sorted(set(out))


class Plan:
    def __init__(self, package):
        self.package = package
        self.remove = []        # relpaths owned solely by this package
        self.dirs = []          # directories owned solely by it, for pruning
        self.shared = {}        # relpath -> other packages also claiming it
        self.bytes = 0

    def add(self, rel, size):
        self.remove.append(rel)
        self.bytes += size


def plan_removal(prefix, claims, files, package, going=None):
    """Files to remove for one package.

    'going' is the full set of packages this run is removing. A file claimed
    by several packages is kept while any of its other owners is staying, but
    removed once they are all on their way out -- otherwise --all would leave
    every shared file behind.
    """
    going = going or {package}
    plan = Plan(package)
    for rel, (_, owners) in claims.dirs.items():
        if package in owners and not (owners - going):
            plan.dirs.append(rel)
    for rel in files:
        owned = claims.owners(rel)
        if not owned or package not in owned[1]:
            continue
        staying = owned[1] - going
        if staying:
            plan.shared[rel] = sorted(staying)
            continue
        path = os.path.join(prefix, rel)
        try:
            size = os.lstat(path).st_size
        except OSError:
            size = 0
        plan.add(rel, size)
    return plan


def human(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return "%.0f %s" % (n, unit) if unit == "B" else "%.1f %s" % (n, unit)
        n /= 1024.0


def summarise(plan, prefix):
    """Group a plan's files by their top-level directory, for the preview."""
    groups = {}
    for rel in plan.remove:
        top = rel.split("/")[0]
        entry = groups.setdefault(top, [0, 0])
        entry[0] += 1
        try:
            entry[1] += os.lstat(os.path.join(prefix, rel)).st_size
        except OSError:
            pass
    return groups


# ---------------------------------------------------------------------------
# Removal
# ---------------------------------------------------------------------------

def remove_files(prefix, plan, verbose=False):
    removed = failed = 0
    for rel in plan.remove:
        path = os.path.join(prefix, rel)
        if not inside(prefix, path):
            print("  skip (outside prefix): %s" % rel, file=sys.stderr)
            continue
        try:
            os.unlink(path)
            removed += 1
            if verbose:
                print("  rm %s" % rel)
        except FileNotFoundError:
            pass
        except IsADirectoryError:
            continue
        except PermissionError:
            # a read-only parent is common in installed trees
            try:
                parent = os.path.dirname(path)
                os.chmod(parent, os.stat(parent).st_mode | stat.S_IWUSR)
                os.unlink(path)
                removed += 1
            except OSError as exc:
                print("  cannot remove %s: %s" % (rel, exc), file=sys.stderr)
                failed += 1
        except OSError as exc:
            print("  cannot remove %s: %s" % (rel, exc), file=sys.stderr)
            failed += 1
    return removed, failed


def prune_empty_dirs(prefix, plan):
    """Remove directories left empty, deepest first. Never the prefix itself.

    Walking each candidate tree bottom-up matters: a directory holding nothing
    but other empty directories is not the parent of any removed file, so
    considering only those parents leaves whole skeletons standing -- removing
    octave left 28 empty directories behind that way, lib/octave/site/oct
    among them.
    """
    candidates = set(plan.dirs)
    for rel in plan.remove:
        parts = rel.split("/")[:-1]
        while parts:
            candidates.add("/".join(parts))
            parts.pop()

    # Deepest candidate roots first, so a nested one is dealt with before the
    # tree that contains it.
    pruned = 0
    for rel in sorted(candidates, key=lambda p: p.count("/"), reverse=True):
        root = os.path.join(prefix, rel)
        if not inside(prefix, root) or os.path.islink(root) or not os.path.isdir(root):
            continue
        # topdown=False visits children before parents, so a directory whose
        # only contents were empty directories becomes empty in the same pass.
        for dirpath, dirnames, _ in os.walk(root, topdown=False):
            dirnames[:] = [d for d in dirnames
                           if not os.path.islink(os.path.join(dirpath, d))]
            if not inside(prefix, dirpath) or os.path.islink(dirpath):
                continue
            try:
                if not os.listdir(dirpath):
                    os.rmdir(dirpath)
                    pruned += 1
            except OSError:
                pass
    return pruned


def remove_stamps(spec, dry_run):
    """Clear the build markers so make will rebuild the package."""
    cleared = []
    for stamp in spec.get("stamps") or []:
        path = os.path.join(REPO_ROOT, stamp)
        if os.path.exists(path):
            cleared.append(stamp)
            if not dry_run:
                try:
                    os.unlink(path)
                except OSError as exc:
                    print("  cannot remove stamp %s: %s" % (stamp, exc),
                          file=sys.stderr)
    return cleared


def perl5lib_local_paths(prefix, spec):
    """Perl library directories the environment points at, outside the prefix.

    local::lib installs modules into ~/perl5 and exports PERL5LIB and
    PERL_LOCAL_LIB_ROOT from a shell profile, which puts that directory ahead
    of the tree on @INC. One left from an older perl shadows the tree with
    modules the current interpreter refuses to load:

        Perl API version v5.42.0 of Encode.c does not match v5.44.0

    Removing perl without clearing that leaves the trap in place for the next
    build, so it is offered here -- but only for paths that are plainly the
    user's own. A directory is a candidate only when it lives under the user's
    home, is writable by them, and is neither the home itself nor any part of
    the install prefix.
    """
    if not spec.get("perl_local_lib"):
        return []

    home = os.path.realpath(os.path.expanduser("~"))
    candidates = []
    for var in ("PERL_LOCAL_LIB_ROOT", "PERL5LIB"):
        for entry in (os.environ.get(var) or "").split(os.pathsep):
            entry = entry.strip()
            if entry:
                candidates.append(os.path.abspath(os.path.expanduser(entry)))

    keep = []
    for path in candidates:
        real = os.path.realpath(path)
        if not os.path.isdir(real):
            continue
        # The user's own home, and nothing above or beside it.
        if real == home or not real.startswith(home + os.sep):
            continue
        # Never anything belonging to the tree; that is the prefix's business.
        if real == prefix or real.startswith(prefix + os.sep):
            continue
        if not os.access(real, os.W_OK):
            continue
        keep.append(real)

    # PERL5LIB usually lists lib/perl5 and its arch directory underneath
    # PERL_LOCAL_LIB_ROOT. Keep the outermost and drop what it contains.
    out = []
    for path in sorted(set(keep), key=len):
        if not any(path == k or path.startswith(k + os.sep) for k in out):
            out.append(path)
    return out


def home_paths(spec):
    out = []
    for entry in spec.get("home") or []:
        path = os.path.abspath(os.path.expanduser(entry))
        if os.path.exists(path):
            out.append(path)
    return out


def dir_size(path):
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames
                       if not os.path.islink(os.path.join(dirpath, d))]
        for name in filenames:
            try:
                total += os.lstat(os.path.join(dirpath, name)).st_size
            except OSError:
                pass
    return total


def remove_home_paths(paths, dry_run):
    home = os.path.realpath(os.path.expanduser("~"))
    for path in paths:
        real = os.path.realpath(path)
        # Only ever inside the user's home, and never the home itself.
        if real == home or not real.startswith(home + os.sep):
            print("  refusing to remove %s (outside your home directory)" % path,
                  file=sys.stderr)
            continue
        if len([p for p in os.path.relpath(real, home).split(os.sep) if p]) < 1:
            continue
        print("  %s %s (%s)" % ("would remove" if dry_run else "removing",
                                path.replace(home, "~"),
                                human(dir_size(real) if os.path.isdir(real) else
                                      os.lstat(real).st_size)))
        if not dry_run:
            try:
                if os.path.isdir(real) and not os.path.islink(real):
                    shutil.rmtree(real)
                else:
                    os.unlink(real)
            except OSError as exc:
                print("    failed: %s" % exc, file=sys.stderr)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_list(config, prefix, claims, files):
    packages = config["packages"]
    counts = {p: 0 for p in packages}
    unclaimed = 0
    for rel in files:
        owned = claims.owners(rel)
        if not owned:
            unclaimed += 1
            continue
        for pkg in owned[1]:
            counts[pkg] = counts.get(pkg, 0) + 1
    print("prefix: %s\n" % prefix)
    print("  %-16s %9s  %s" % ("PACKAGE", "FILES", "SOURCES"))
    for pkg in sorted(packages):
        spec = packages[pkg]
        sources = ",".join(spec.get("claims") or []) or "owns"
        print("  %-16s %9d  %s" % (pkg, counts.get(pkg, 0), sources))
    print("\n  %-16s %9d  (use --orphans to list)" % ("unclaimed", unclaimed))
    return 0


def cmd_orphans(prefix, claims, files, limit):
    orphans = [rel for rel in files if not claims.owners(rel)]
    total = 0
    for rel in orphans:
        try:
            total += os.lstat(os.path.join(prefix, rel)).st_size
        except OSError:
            pass
    print("%d files under %s are not claimed by any package (%s)\n"
          % (len(orphans), prefix, human(total)))
    groups = {}
    for rel in orphans:
        groups.setdefault(rel.split("/")[0], []).append(rel)
    for top in sorted(groups):
        print("  %s/  (%d)" % (top, len(groups[top])))
        for rel in groups[top][:limit]:
            print("      %s" % rel)
        if len(groups[top]) > limit:
            print("      ... %d more" % (len(groups[top]) - limit))
    if orphans:
        print("\nThese are either installed by something this tool does not know\n"
              "about, or gaps in the 'owns' patterns in %s." % CONFIG_NAME)
    return 0


def report_plan(plan, spec, prefix, args):
    groups = summarise(plan, prefix)
    print("package   %s" % plan.package)
    print("prefix    %s" % prefix)
    print("files     %d  (%s)" % (len(plan.remove), human(plan.bytes)))
    if groups:
        print()
        for top in sorted(groups, key=lambda t: -groups[t][1]):
            count, size = groups[top]
            print("  %-24s %7d files  %10s" % (top + "/", count, human(size)))

    if plan.shared:
        print("\n  %d files are claimed by another package as well and will be "
              "left alone:" % len(plan.shared))
        shown = sorted(plan.shared.items())[:8]
        for rel, others in shown:
            print("      %-46s also %s" % (rel, ", ".join(others)))
        if len(plan.shared) > len(shown):
            print("      ... %d more" % (len(plan.shared) - len(shown)))

    stamps = [s for s in (spec.get("stamps") or [])
              if os.path.exists(os.path.join(REPO_ROOT, s))]
    if stamps and not args.keep_stamps:
        print("\n  build stamps to clear: %s" % " ".join(stamps))

    home = home_paths(spec)
    if home:
        tilde = os.path.expanduser("~")
        print("\n  outside the prefix%s:"
              % ("" if args.with_home else ", left alone without --with-home"))
        for path in home:
            size = dir_size(path) if os.path.isdir(path) else os.lstat(path).st_size
            print("      %-40s %10s" % (path.replace(tilde, "~"), human(size)))

    perl5lib = perl5lib_local_paths(prefix, spec)
    if perl5lib:
        tilde = os.path.expanduser("~")
        print("\n  perl library directories from your environment%s:"
              % ("" if args.perl5lib_local else ", left alone without --perl5lib-local"))
        for path in perl5lib:
            print("      %-40s %10s" % (path.replace(tilde, "~"),
                                        human(dir_size(path))))
        print("      (PERL5LIB / PERL_LOCAL_LIB_ROOT; these shadow the tree on @INC)")


def uninstall_one(config, prefix, claims, files, package, args, going=None):
    spec = config["packages"][package]
    plan = plan_removal(prefix, claims, files, package, going)

    if args.json:
        print(json.dumps({
            "package": package, "prefix": prefix,
            "files": plan.remove, "bytes": plan.bytes,
            "shared": plan.shared,
            "stamps": spec.get("stamps") or [],
            "home": home_paths(spec),
            "perl5lib_local": perl5lib_local_paths(prefix, spec),
        }, indent=2))
        return 0

    report_plan(plan, spec, prefix, args)

    # Empty directories left by an earlier removal still count as work.
    leftover_dirs = [d for d in plan.dirs
                     if os.path.isdir(os.path.join(prefix, d))]
    if (not plan.remove and not leftover_dirs
            and not (args.with_home and home_paths(spec))
            and not (args.perl5lib_local and perl5lib_local_paths(prefix, spec))):
        print("\nNothing to remove for %s." % package)
        return 0
    if not plan.remove and leftover_dirs:
        print("\n  no files left, but %d empty directories from a previous "
              "removal remain" % len(leftover_dirs))

    if not args.yes:
        print("\nDry run -- nothing was removed. Add --yes to go ahead.")
        return 0

    print()
    removed, failed = remove_files(prefix, plan, verbose=args.verbose)
    pruned = prune_empty_dirs(prefix, plan)
    print("removed %d files, %s, and %d empty directories"
          % (removed, human(plan.bytes), pruned))
    if failed:
        print("%d files could not be removed (see above)" % failed,
              file=sys.stderr)

    if not args.keep_stamps:
        cleared = remove_stamps(spec, dry_run=False)
        if cleared:
            print("cleared build stamps: %s" % " ".join(cleared))

    if args.with_home:
        paths = home_paths(spec)
        if paths:
            print("\noutside the prefix:")
            remove_home_paths(paths, dry_run=False)

    if args.perl5lib_local:
        paths = perl5lib_local_paths(prefix, spec)
        if paths:
            print("\nperl library directories from your environment:")
            remove_home_paths(paths, dry_run=False)
            print("  remember to take the local::lib lines out of your shell\n"
                  "  profile too, or the next shell will point at a directory\n"
                  "  that no longer exists")

    return 1 if failed else 0


def build_parser():
    p = argparse.ArgumentParser(
        prog="uninstall.py",
        description="Remove an installed package from the nlytiq tree.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""examples:
  uninstall.py --list
  uninstall.py --package octave
  uninstall.py --package octave --yes
  uninstall.py --all --yes
  uninstall.py --orphans
""")
    p.add_argument("--package", "-p", metavar="NAME",
                   help="package to remove, as named in " + CONFIG_NAME)
    p.add_argument("--all", "-a", action="store_true",
                   help="remove every package described in " + CONFIG_NAME)
    p.add_argument("--yes", "-y", action="store_true",
                   help="actually remove things (without this it is a dry run)")
    p.add_argument("--with-home", action="store_true",
                   help="also remove this package's data under your home "
                        "directory (~/.julia, ~/.cpan, kernel specs, ...)")
    p.add_argument("--perl5lib-local", action="store_true",
                   help="also remove writable perl library directories under "
                        "your home that PERL5LIB or PERL_LOCAL_LIB_ROOT point "
                        "at (local::lib's ~/perl5 and the like)")
    p.add_argument("--keep-stamps", action="store_true",
                   help="leave the build stamp files alone")
    p.add_argument("--prefix", metavar="PATH",
                   help="install prefix (default: NLYTIQ_INST_PATH from "
                        "config/base.config)")
    p.add_argument("--list", "-l", action="store_true",
                   help="list packages and how many files each claims")
    p.add_argument("--orphans", action="store_true",
                   help="list files under the prefix that no package claims")
    p.add_argument("--limit", type=int, default=10, metavar="N",
                   help="with --orphans, examples to show per directory")
    p.add_argument("--json", action="store_true",
                   help="emit the removal plan as JSON and stop")
    p.add_argument("--verbose", "-v", action="store_true",
                   help="print every file as it is removed")
    p.add_argument("--config", metavar="PATH",
                   default=os.path.join(REPO_ROOT, CONFIG_NAME))
    return p


def main(argv):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not os.path.exists(args.config):
        raise Fail("no %s found (looked in %s)" % (CONFIG_NAME, args.config))
    parser_module = load_yaml_parser()
    config = load_config(args.config, parser_module)

    prefix = validate_prefix(resolve_prefix(args.prefix, config))
    packages = config["packages"]

    claims = build_claims(prefix, packages)
    files = walk_prefix(prefix)

    if args.list:
        return cmd_list(config, prefix, claims, files)
    if args.orphans:
        return cmd_orphans(prefix, claims, files, args.limit)

    if args.all:
        targets = sorted(packages)
    elif args.package:
        name = args.package
        if name not in packages:
            matches = [k for k in packages if k.lower() == name.lower()]
            if not matches:
                raise Fail("unknown package %r.\nKnown packages: %s"
                           % (name, ", ".join(sorted(packages))))
            name = matches[0]
        targets = [name]
    else:
        parser.print_usage(sys.stderr)
        raise Fail("give --package NAME, or --all (or --list to see what "
                   "there is)")

    if args.all and args.yes and not args.json:
        print("Removing %d packages from %s.\n" % (len(targets), prefix))

    status = 0
    for i, package in enumerate(targets):
        if i:
            print("\n" + "-" * 68 + "\n")
        status |= uninstall_one(config, prefix, claims, files, package, args,
                                going=set(targets))
        if args.yes:
            # Later packages must see the tree as it now stands.
            files = walk_prefix(prefix)
    return status


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv[1:]))
    except Fail as exc:
        print("uninstall.py: %s" % exc, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\ninterrupted", file=sys.stderr)
        sys.exit(130)
