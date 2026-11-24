#!/usr/bin/env bash
# Regression test for the reposync `delete` option.
#
# Stands up a throwaway yum repo in a container, mirrors it with cattleDrive,
# then removes a package upstream and re-mirrors. Asserts that the orphaned rpm
# is pruned by default and retained with `delete: false`.
#
# Usage: ./utils/test-reposync-delete.sh [image]   (default: cattledrive:regression-test)
set -euo pipefail

IMAGE="${1:-cattledrive:regression-test}"
T="$(mktemp -d /tmp/cattledrive-reposync-test.XXXXXX)"
NET=cdtest-$$
WEB=cdtest-web-$$

cleanup() {
  docker rm -f "$WEB" >/dev/null 2>&1 || true
  docker network rm "$NET" >/dev/null 2>&1 || true
  docker run --rm -v "$T":/t "$IMAGE" rm -rf /t/upstream /t/mirror-default /t/mirror-nodelete >/dev/null 2>&1 || true
  rm -rf "$T"
}
trap cleanup EXIT

mkdir -p "$T"/{upstream,mirror-default,mirror-nodelete}
chmod -R 777 "$T"

cat > "$T/config.yml" <<EOF
mirror:
  - type: reposync
    src: http://$WEB:8080/
    dest: /drop/mirror-default/
  - type: reposync
    src: http://$WEB:8080/
    dest: /drop/mirror-nodelete/
    delete: false
EOF

run_cattledrive() {
  docker run --rm --network "$NET" \
    -v "$T":/repo \
    -v "$T/mirror-default":/drop/mirror-default \
    -v "$T/mirror-nodelete":/drop/mirror-nodelete \
    "$IMAGE" cattleDrive /repo/config.yml
}

echo "== building upstream repo fixture"
docker network create "$NET" >/dev/null
docker run --rm -v "$T/upstream":/upstream "$IMAGE" bash -c \
  'dnf download -q --destdir /upstream tree zip which >/dev/null 2>&1 && createrepo /upstream >/dev/null 2>&1'
docker run -d --name "$WEB" --network "$NET" -v "$T/upstream":/upstream:ro \
  "$IMAGE" python3 -m http.server 8080 --directory /upstream >/dev/null
sleep 2

echo "== initial sync"
run_cattledrive >/dev/null 2>&1

echo "== mutating upstream: drop zip, add psmisc"
docker run --rm -v "$T/upstream":/upstream "$IMAGE" bash -c \
  'rm -f /upstream/zip-*.rpm && dnf download -q --destdir /upstream psmisc >/dev/null 2>&1 \
   && rm -rf /upstream/repodata && createrepo /upstream >/dev/null 2>&1'

echo "== re-sync"
run_cattledrive >/dev/null 2>&1

rc=0
check() { # desc dir pattern expected(present|absent)
  if ls "$2" | grep -q "$3"; then found=present; else found=absent; fi
  if [ "$found" = "$4" ]; then echo "PASS: $1"; else echo "FAIL: $1 (got $found, want $4)"; rc=1; fi
}
check "default prunes orphaned rpm"        "$T/mirror-default"  '^zip-'    absent
check "default picks up new rpm"           "$T/mirror-default"  '^psmisc-' present
check "default keeps still-current rpm"    "$T/mirror-default"  '^tree-'   present
check "delete:false retains orphaned rpm"  "$T/mirror-nodelete" '^zip-'    present
check "delete:false picks up new rpm"      "$T/mirror-nodelete" '^psmisc-' present

exit $rc
