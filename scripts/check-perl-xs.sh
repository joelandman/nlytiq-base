#!/usr/bin/env bash
#
# Find compiled perl XS modules that were built against a different perl than
# the one installed in the tree.
#
# Usage:  scripts/check-perl-xs.sh [prefix]
#
# Perl checks this itself when it loads an XS module, and dies:
#
#     Perl API version v5.42.0 of Encode.c does not match v5.44.0
#
# which is accurate but arrives in the middle of a cpan run, attached to
# whichever module happened to pull the stale one in. Since a .so records the
# API version it was compiled for, the mismatches can be listed up front.
#
# This happens after a perl version bump. 'make install' for the new perl adds
# lib/perl5/<newver>/ beside the old tree without removing anything, and perl
# keeps previous versions' site_perl directories on @INC on purpose, so
# modules built for the old perl stay reachable. Those built from pure perl
# keep working; the compiled ones abort the interpreter.
#
# Exits 0 when everything matches, 1 when something does not.

set -uo pipefail

PREFIX="${1:-}"
if [ -z "${PREFIX}" ]; then
	REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
	PREFIX="$(make -f "${REPO_ROOT}/Makefile.perl5" print-NLYTIQ_INST_PATH 2>/dev/null |
		  sed -n 's/^NLYTIQ_INST_PATH = //p')"
	PREFIX="${PREFIX:-$HOME/local}"
fi

PERL="${PREFIX}/bin/perl"
[ -x "${PERL}" ] || { echo "no perl at ${PERL}; pass a prefix" >&2; exit 1; }

WANT="v$("${PERL}" -e 'printf "%vd", $^V')"
echo "perl in ${PREFIX} is ${WANT}"

command -v strings >/dev/null 2>&1 || {
	echo "need 'strings' (binutils) to read the API version out of .so files" >&2
	exit 1
}

bad=0
checked=0
while IFS= read -r so; do
	checked=$((checked + 1))
	# An XS .so carries the API version it was compiled against, as the
	# string perl compares at boot time.
	api="$(strings "${so}" 2>/dev/null | grep -oE '^v5\.[0-9]+\.[0-9]+$' | sort -u | head -1)"
	[ -n "${api}" ] || continue
	if [ "${api}" != "${WANT}" ]; then
		if [ "${bad}" -eq 0 ]; then
			echo
			echo "built against a different perl:"
			printf '  %-10s %s\n' "API" "MODULE"
		fi
		printf '  %-10s %s\n' "${api}" "${so#"${PREFIX}"/}"
		bad=$((bad + 1))
	fi
done < <(find "${PREFIX}/lib/perl5" -name '*.so' -path '*/auto/*' 2>/dev/null | sort)

echo
if [ "${bad}" -eq 0 ]; then
	echo "checked ${checked} XS modules, all built against ${WANT}"
	exit 0
fi

cat <<EOF
checked ${checked} XS modules, ${bad} built against another perl.

Any of those will abort the interpreter the moment something loads it:

    Perl API version <old> of <Module>.c does not match ${WANT}

They are left over from a previous perl in this same prefix. Remove the old
version's trees and reinstall the modules against ${WANT}:

    rm -rf ${PREFIX}/lib/perl5/site_perl/<oldversion>
    rm -rf ${PREFIX}/lib/perl5/<oldversion>
    make -f Makefile.perl5mods

Check what a directory holds before removing it. Modules that exist only in
the old tree disappear with it, and their pure-perl dependencies may have been
quietly satisfying something in the new one -- deleting the old tree here left
Types::Serialiser missing, which broke JSON::XS and everything under it.
EOF
exit 1
