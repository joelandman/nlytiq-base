# Updating packages

`scripts/update-package.py` bumps a package to a new upstream version: it finds
the versions upstream offers, downloads the one you want, and points the build
at it.

It needs nothing but `python3` -- no pip install, no virtualenv. That is
deliberate: this tree builds its own Python, so the tool that fetches its
sources cannot depend on anything installed into it.

- [Why a tool at all](#why-a-tool-at-all)
- [Quick start](#quick-start)
- [Commands](#commands)
- [Workflows](#workflows)
- [packages.yaml](#packagesyaml)
- [Adding a package](#adding-a-package)
- [When something goes wrong](#when-something-goes-wrong)
- [What it does not do](#what-it-does-not-do)


## Why a tool at all

A version bump in this tree touches three things that all have to agree:

| | |
|---|---|
| `Makefile.<pkg>` | the version variable, e.g. `GNUPLOTVER = 6.0.4`. Everything else in the file -- directory names, tarball names, unpack rules -- derives from it. |
| `sources/manifest.txt` | the line giving that tarball's **filename**, **SHA-256** and **URL**. `scripts/fetch-source.sh` reads it during the build. |
| `sources/` | the tarball itself. |

Miss the manifest and the next build stops with *"no manifest entry"*. Get the
checksum wrong and it stops with a mismatch, which is exactly what you want it
to do but not much fun to debug. Doing all three by hand means downloading the
tarball, running `sha256sum`, and retyping a 64-character hex string into a
column-aligned file.

The tool does all three from one command, and computes the checksum from the
bytes that actually arrived rather than from anything a web page claimed.


## Quick start

```console
$ scripts/update-package.py --package gnuplot --list-versions
gnuplot -- currently pinned at 6.0.4 (Makefile.gnuplot)

  VERSION          DATE         AGE
  6.0.5            2026-07-31   15 days
  6.0.4            2025-12-17   241 days  <- current
  6.0.3            2025-06-07   434 days
  6.0.2            2024-12-20   603 days

  ... 7 more, use --limit 0 to see all

$ scripts/update-package.py --package gnuplot
  [##############################] 100%  7.2 MB / 7.2 MB  3.1 MB/s  eta 00:00
package   gnuplot
current   6.0.4
target    6.0.5  (latest upstream)
tarball   sources/gnuplot-6.0.5.tar.gz
url       https://downloads.sourceforge.net/project/gnuplot/gnuplot/6.0.5/gnuplot-6.0.5.tar.gz

sha256    73237f37f03306d68bfae133a9a50d5e9341384e198d5ab37eeca9ab534deed8

updated:
  Makefile.gnuplot:            GNUPLOTVER = 6.0.5
  sources/manifest.txt:        gnuplot-6.0.4.tar.gz
                                 -> gnuplot-6.0.5.tar.gz
  sources:                     gnuplot-6.0.5.tar.gz

removed the superseded tarball gnuplot-6.0.4.tar.gz

Review with 'git diff', then build with:
  make -f Makefile.gnuplot clean && make -f Makefile.gnuplot
```

The resulting diff is two lines, and nothing else in either file moves:

```diff
 ####
-GNUPLOTVER	= 6.0.4
+GNUPLOTVER	= 6.0.5
 GNUPLOT		= gnuplot-${GNUPLOTVER}
```
```diff
-gnuplot-6.0.4.tar.gz            458d9476...9c5b  https://downloads.sourceforge.net/project/gnuplot/gnuplot/6.0.4/gnuplot-6.0.4.tar.gz
+gnuplot-6.0.5.tar.gz            73237f37...eed8  https://downloads.sourceforge.net/project/gnuplot/gnuplot/6.0.5/gnuplot-6.0.5.tar.gz
```


## Commands

### What do we track, and at what version

```console
$ scripts/update-package.py --list-packages
packages described in packages.yaml:

  R         4.4.1       Makefile.R  (html_index)
  gnuplot   6.0.4       Makefile.gnuplot  (sourceforge)
  julia     1.12.5      Makefile.julia  (github)
  llvm      20.1.0      Makefile.llvm  (github)
  maxima    5.49.0      Makefile.maxima  (sourceforge)
  octave    10.3.0      Makefile.octave  (html_index)
  openblas  0.3.30      Makefile.openblas  (github)
  perl5     5.42.0      Makefile.perl5  (html_index)
  python    3.14.3      Makefile.python  (html_index)
```

The last column is where version information comes from. Package names are
matched case-insensitively, so `--package r` finds `R`.

### What is available upstream

```console
$ scripts/update-package.py --package julia --list-versions --limit 4
julia -- currently pinned at 1.12.5 (Makefile.julia)

  VERSION          DATE         AGE
  1.12.7           2026-08-15   0 days
  1.12.6           2026-04-10   127 days
  1.12.5           2026-02-10   186 days  <- current
  1.12.4           2026-01-07   220 days
```

Sorted by version, not by date, and numerically -- `1.10.0` sorts above `1.9.9`,
and `20.1.0` above `9.0.1`. Default is 15 entries; `--limit 0` shows all.

Release candidates and development versions are hidden unless you ask:

```console
$ scripts/update-package.py --package llvm --list-versions --include-prerelease
```

For scripting, `--json` gives the same data with machine-readable dates:

```console
$ scripts/update-package.py --package octave --list-versions --limit 2 --json
{
  "package": "octave",
  "current": "10.3.0",
  "versions": [
    {
      "version": "11.3.0",
      "date": "2026-06-04",
      "age_days": 72,
      "prerelease": false
    },
    {
      "version": "11.2.0",
      "date": "2026-05-30",
      "age_days": 77,
      "prerelease": false
    }
  ]
}
```

### Look before you leap

`--dry-run` resolves the version and prints the exact URL and the exact edits,
without downloading or writing anything:

```console
$ scripts/update-package.py --package llvm --dry-run
package   llvm
current   20.1.0
target    22.1.8  (latest upstream)
tarball   sources/llvm-project-22.1.8.src.tar.xz
url       https://github.com/llvm/llvm-project/releases/download/llvmorg-22.1.8/llvm-project-22.1.8.src.tar.xz

dry run: would download the tarball, then update
  Makefile.llvm: LLVMVER = 22.1.8
  sources/manifest.txt: entry for llvm-project-22.1.8.src.tar.xz
```

Worth doing on a first bump of any package, since it shows whether the URL
template still matches what upstream publishes.

### Bump

```console
$ scripts/update-package.py --package julia                  # latest upstream
$ scripts/update-package.py --package julia --version 1.11.7 # a specific one
```

`--version` takes any version, including one older than the current pin --
downgrading is just a bump in the other direction and works the same way.

Other flags:

| flag | effect |
|---|---|
| `--force` | re-download even if the tarball is already in `sources/`, and re-checksum it |
| `--keep-old` | keep the superseded tarball instead of deleting it |
| `--quiet` | no progress bar |
| `--limit N` | with `--list-versions`, show N entries (`0` for all) |
| `--include-prerelease` | do not hide release candidates and development versions |
| `--config PATH` | use a different `packages.yaml` |
| `--self-test` | run the built-in checks and exit |

Re-running a bump that is already done is safe and cheap:

```console
$ scripts/update-package.py --package gnuplot --version 6.0.5
package   gnuplot
current   6.0.5
...
Already at 6.0.5 and the tarball is present. Nothing to do.
(Use --force to re-download and re-checksum it.)
```


## Workflows

### The routine bump

```console
$ scripts/update-package.py --package octave --list-versions   # what is out there
$ scripts/update-package.py --package octave --dry-run         # what would change
$ scripts/update-package.py --package octave                   # do it
$ git diff                                                     # two lines
$ make -f Makefile.octave clean && make -f Makefile.octave     # prove it builds
$ git commit -am "Update octave to 11.3.0"
```

Build before you commit. The tool guarantees you have the right bytes; it
cannot guarantee the new version still compiles with the flags in
`Makefile.octave`, and a major-version jump often needs a flag adjusted in the
same commit.

### Survey everything before a round of updates

```console
$ for p in $(scripts/update-package.py --list-packages | awk 'NR>2 {print $1}'); do
      scripts/update-package.py --package "$p" --dry-run | head -3
      echo
  done
```

Each block shows `current` against `target`, so the packages that have drifted
are the ones where the two differ. Do them one at a time -- one package per
commit, each one built -- rather than bumping nine things and then working out
which one broke the tree.

### Pin deliberately, not just to the newest

The newest is not always the one you want. LLVM 22 and Octave 11 are major
jumps; a maintenance release of the series you are on is usually the safer
move:

```console
$ scripts/update-package.py --package llvm --list-versions --limit 0 | grep '^  20\.'
$ scripts/update-package.py --package llvm --version 20.1.8
```

### Bumping a version you already know

If upstream has just announced something and you do not need the listing at
all, skip the probe entirely -- `--version` never contacts the version source,
only the download URL:

```console
$ scripts/update-package.py --package openblas --version 0.3.34
```

This is also the escape hatch when a probe is broken or a site is down.

### Rolling back

The tool is symmetric, and reproduces the original bytes exactly:

```console
$ scripts/update-package.py --package gnuplot --version 6.0.4
```

Or, if you have not yet built anything, just `git checkout Makefile.gnuplot
sources/manifest.txt` and re-run `scripts/fetch-source.sh --all`.

### Pre-fetch for an offline build

Updating and pre-fetching are separate jobs. After bumping whatever you mean
to bump, populate `sources/` on the machine that has network access:

```console
$ scripts/fetch-source.sh --all
```

then build offline. `fetch-source.sh` verifies against the same manifest the
tool just wrote.

### Checking the tool itself

```console
$ scripts/update-package.py --self-test
self-test: all checks passed
```

This covers version ordering, template expansion, the Makefile and manifest
rewriters, date parsing, and the config parser -- and then checks the real
`packages.yaml` against the real tree: every package's Makefile must exist, its
pinned version must be readable, and that version must expand to exactly the
filename and URL already recorded in `sources/manifest.txt`. It makes no
network requests, so it is safe to run anywhere, any time.


## packages.yaml

One entry per package, at the top of the tree. Two halves: how to **find**
versions, and how to **use** one.

```yaml
  openblas:
    makefile: Makefile.openblas          # file to edit
    version_var: OBLASVER                # variable in it to rewrite
    filename: "OpenBLAS-__VERSION__.tar.gz"
    url: "https://github.com/OpenMathLib/OpenBLAS/releases/download/v__VERSION__/OpenBLAS-__VERSION__.tar.gz"
    versions:
      kind: github
      repo: OpenMathLib/OpenBLAS
      tag_pattern: "^v(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+)$"
```

In `url` and `filename`, `__VERSION__` expands to the full version, and
`__MAJOR__`, `__MINOR__`, `__PATCH__` to its components. CRAN's major-version
directory needs the last of these:

```yaml
    url: "https://cran.r-project.org/src/base/R-__MAJOR__/R-__VERSION__.tar.xz"
```

Four kinds of version source:

| kind | how | dates |
|---|---|---|
| `github` | the releases (or `source: tags`) API | yes |
| `git` | `git ls-remote --tags` against any git host | no |
| `html_index` | an Apache/nginx directory listing | when the listing has a date column |
| `sourceforge` | the project's file-release RSS feed | yes |

`tag_pattern` (github, git) and `pattern` (html_index, sourceforge) are regular
expressions with a named group `version`. Anything that does not match is
ignored, which is what keeps other projects' tags, unrelated files and release
candidates out of the list. The pattern is also where a tag that differs from
the version gets bridged -- LLVM tags releases `llvmorg-22.1.8`, so the prefix
lives in the URL template and the pattern strips it back off:

```yaml
    url: ".../releases/download/llvmorg-__VERSION__/llvm-project-__VERSION__.src.tar.xz"
    versions:
      kind: github
      repo: llvm/llvm-project
      tag_pattern: "^llvmorg-(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+)$"
```

`stable_pattern` handles upstreams that encode prerelease status in the number
itself. perl uses odd minor versions for development releases, so 5.45.1 is not
something you want to build:

```yaml
      stable_pattern: "^5\\.[0-9]*[02468]\\.[0-9]+$"
```

Versions that do not match are treated as prereleases and hidden unless you
pass `--include-prerelease`.


## Adding a package

1. Find where upstream publishes releases and pick the matching `kind`. If
   nothing else fits, `kind: git` with a clone URL works against any git host
   and needs no API -- it just cannot report dates.
2. Add the entry to `packages.yaml`.
3. Check the probe with the version you already have:

   ```console
   $ scripts/update-package.py --package newthing --list-versions --limit 0
   ```

   The version currently pinned in the Makefile should appear in the list, with
   a `<- current` marker. If it does not, the pattern is wrong -- fix it before
   going further, because a probe that cannot see the present cannot be trusted
   about the future.
4. Confirm the templates:

   ```console
   $ scripts/update-package.py --package newthing --dry-run
   ```

   Compare the printed URL against the real download link. Then
   `scripts/update-package.py --self-test`, which fails if the current pin does
   not expand to exactly the filename and URL in the manifest.
5. Bump it, and build it.

A `git`-kind entry looks like this:

```yaml
  something:
    makefile: Makefile.something
    version_var: SOMETHINGVER
    filename: "something-__VERSION__.tar.gz"
    url: "https://git.example.org/something/archive/v__VERSION__.tar.gz"
    versions:
      kind: git
      url: "https://git.example.org/something.git"
      tag_pattern: "^v(?P<version>[0-9]+\\.[0-9]+\\.[0-9]+)$"
```


## When something goes wrong

Nothing is written until the download has completed and been hashed, so an
interrupted or failed run leaves the tree exactly as it was. There is no
half-updated state to clean up; re-run the command.

**`HTTP 403` from GitHub.** Anonymous API requests are rate-limited. Set a
token and retry:

```console
$ GITHUB_TOKEN=ghp_... scripts/update-package.py --package julia --list-versions
```

`GH_TOKEN` works too. Only `kind: github` needs this; the other three do not
touch an API.

**`HTTP 404` on the download.** Either the version does not exist, or upstream
changed its URL layout. The message says both. Check with `--list-versions`,
and if the version is real, the `url` template in `packages.yaml` needs
updating.

**"no versions matched at the upstream".** The `pattern` no longer fits what
upstream publishes -- a redesigned download page, a moved directory. Fetch the
URL from `packages.yaml` by hand and look at what is actually there.

**"already lists ... with a different checksum".** The manifest has an entry
for this exact filename but a different hash than what just downloaded. Either
upstream re-rolled the tarball under the same name, or the download is corrupt
or tampered with. The tool stops and writes nothing. Do not paper over this by
editing the manifest -- find out why first.

**"no assignment to 'X' found"** or **"assigned N times".** The Makefile does
not have the variable `version_var` names, or has it more than once. The tool
will not guess which assignment pins the version. Fix `packages.yaml`, or the
Makefile.

**A version you cannot see.** `--version` bypasses the probe entirely, so a
broken pattern or an unreachable version source never blocks a bump you already
know how to spell.


## What it does not do

- **`rust`, `spark`, `jupyter_kernels`, `perl5mods`** are not managed here.
  They install via rustup, a local snapshot, and pip/cpan respectively -- there
  is no upstream tarball to checksum. `packages.yaml` says so in a comment.
- **It does not build.** Bumping and building are separate on purpose: you get
  a reviewable diff before anything expensive happens.
- **It does not clone.** Downloads are release tarballs verified by SHA-256,
  which is what `sources/manifest.txt` and `fetch-source.sh` are built around.
  `kind: git` is used for *finding* versions, not for fetching them.
- **It does not judge.** Whether a version is a good idea -- API breakage, a
  major bump that needs new configure flags -- is your call. Build it before
  you commit it.
