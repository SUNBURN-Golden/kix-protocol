#!/bin/bash
# Resumable C++ object-cache wrapper (ccache-equivalent) for the offline DuckDB
# bundled build. cc recompiles every object on each invocation and has no native
# cache; this wrapper lets the build make progress across bounded foreground
# commands on a memory-constrained host. It does NOT change compiler, flags or
# source semantics: a cache hit only skips recompilation of an object that was
# already produced by the real compiler from the identical command line and a
# source no newer than the object. Misses compile atomically (temp + rename) so
# an interrupted build never leaves a corrupt object marked complete.
#
# Invoked by cc via CXX. Non-compile probes (no -c/-o) pass straight through.
REAL_CXX="${KIX_REAL_CXX:-c++}"

dst=""; src=""; prev=""
for a in "$@"; do
  case "$prev" in
    -o) dst="$a" ;;
    -c) src="$a" ;;
  esac
  prev="$a"
done

if [[ -z "$dst" || -z "$src" || ! -f "$src" ]]; then
  exec "$REAL_CXX" "$@"
fi

# Key the cache on the full command line (flags + source + object path).
hash=$(printf '%s\0' "$@" | sha256sum | cut -d' ' -f1)
sidecar="${dst}.kixhash"
if [[ -f "$dst" && -f "$sidecar" && "$(cat "$sidecar" 2>/dev/null)" == "$hash" && "$dst" -nt "$src" ]]; then
  exit 0
fi

tmp="${dst}.tmp.$$"
newargs=(); prev=""
for a in "$@"; do
  if [[ "$prev" == "-o" ]]; then newargs+=("$tmp"); else newargs+=("$a"); fi
  prev="$a"
done
"$REAL_CXX" "${newargs[@]}"
rc=$?
if [[ $rc -eq 0 ]]; then
  mv -f "$tmp" "$dst"
  printf '%s' "$hash" > "$sidecar"
else
  rm -f "$tmp"
fi
exit $rc
