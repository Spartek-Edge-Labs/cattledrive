---
description: Generic regression test for cattleDrive. Runs a config against two image versions (ghcr:latest and a local build by default) and validates that outputs are correct. User specifies which config to use; Claude suggests an appropriate one if not provided.
---

## Regression Test

### Requirements check

1. **Docker**: Run `docker info`. If the daemon is unreachable, stop and tell the user.
2. **Config file**: The user should provide a path to a cattleDrive config. If none was given, read the available `config*.yml` files in the working directory, look at what code paths were recently changed (via `git diff` or context from the conversation), and suggest the config whose active entries best exercise those paths. Ask the user to confirm before proceeding.

### Determine images to test

If the user specified image tags, test only those.

Otherwise use this two-phase matrix:
- **Phase 1**: `ghcr.io/spartek-edge-labs/cattledrive:latest` — the upstream baseline
- **Phase 2**: local build from the working directory (`docker build -t cattledrive:regression-test .`)

Pull or build each image before running.

### Inspect the config and plan validation

Read the config file. For each active (uncommented) entry, identify its `type` and `dest`. Based on the types present, decide what correct output looks like — use your judgment. General guidance by type:

- **wget / rsync**: dest directory exists and is non-empty; spot-check that key files are present and sizes are non-zero
- **reposync**: dest contains a `repodata/` directory; validate that the repodata is complete and intact for the repo format being mirrored (e.g. for modular repos, module metadata should be present); attempt a functional package install if practical
- **oci**: dest contains `.tar` or `.tar.gz` files; verify they are valid archives (`tar -tzf`)
- **helm**: dest contains `.tgz` chart files; if `pullImages: true`, verify the images subdirectory is populated
- **galaxy**: dest contains `ansible_collections/` with the expected namespace/collection directories

Document your planned validation steps before running anything, so the user can redirect if needed.

### Run each image

For each image under test, run cattleDrive against the config. Clean up any previous test container first.

Mount the config directory and all dest paths. Use the same mount strategy as the docker-readme: bind-mount the config dir to `/repo` and each dest to its actual host path.

```bash
docker rm -f cattledrive-regtest 2>/dev/null || true
docker run --name cattledrive-regtest \
  -v <config-dir>:/repo \
  -v <dest-root>:<dest-root> \
  <image> \
  cattleDrive /repo/<config-filename>
```

Capture stdout/stderr. Note any non-zero exit codes or error output.

### Validate outputs

Apply the validation plan you defined above to the outputs of each run. Where two images are being compared, note any differences in output structure, file counts, or functional test results.

### Report results

Produce a summary table with one row per image per config entry:

```
Image                  | Entry (type → dest)        | Output check   | Functional test
-----------------------|----------------------------|----------------|----------------
ghcr:latest            | reposync → .../AppStream/  | ...            | ...
cattledrive:regtest    | reposync → .../AppStream/  | ...            | ...
```

If the two-phase default matrix was used, interpret the results:
- Phase 1 fails, Phase 2 passes → **regression confirmed fixed**
- Both pass → note that the baseline already has the fix; the local build is still validated
- Phase 2 fails → **do not ship** — show what broke and where
