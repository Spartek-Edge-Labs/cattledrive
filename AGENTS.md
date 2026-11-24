# AGENTS.md

Guidance for AI agents working in this repo. Humans may find it useful too.

## What this is

cattleDrive is a declarative artifact aggregator for green-field and air-gapped
deployments. It reads a YAML config listing "mirror" entries and pulls each one
to a local path: yum repos, web directories, OCI images, helm charts, ansible
collections, rsync trees.

It is deliberately a **single script that shells out to the real tools**
(`wget`, `rsync`, `reposync`, `skopeo`, `helm`, `ansible-galaxy`). It is not a
library and does not reimplement those tools. Keep it that way unless an issue
says otherwise — the design goal is that an operator can read the script and
know exactly what commands ran against their mirror.

## Layout

| Path | What it is |
|---|---|
| `cattleDrive.py` | The entire program. ~280 lines. |
| `config.yml` | Reference config — has an example of every implemented mirror type. |
| `config.local*.yml` | Gitignored. Real/scratch configs for local testing. |
| `Dockerfile` | Rocky 9 base with every shelled-out tool installed. The supported way to run. |
| `docker-readme.md` | Docker usage, mount strategy, caveats. |
| `k8s/` | Manifests for running as a CronJob behind a webserver. |
| `utils/` | Standalone helper and test scripts. |
| `TODO.md` | Known gaps and unimplemented mirror types. |

### `cattleDrive.py` structure

- Helper: `pushd()` (creates the dir if missing, then `chdir`).
- One `get_<type>()` function per mirror type.
- A dispatch `for s in config.get("mirror")` at the bottom (~line 239) matching
  on `s["type"]`.

Two calling conventions coexist: older types take positional args
(`get_wget(src, dest)`), newer ones take `**args` and receive the whole config
entry (`get_reposync(**s)`). When adding config keys to a `**args` type, read
them with `args.get('key', <default>)` and document the default.

## Adding a mirror type

1. Write `get_<type>(**args)` following the existing pattern: `currDir =
   os.getcwd()`, `pushd(args['dest'])`, shell out, `os.chdir(currDir)`.
2. Add an `elif s["type"] == "<type>":` branch to the dispatch.
3. Install any new binary in the `Dockerfile`.
4. Add a commented example to `config.yml` **and** a section to the README
   documenting every key and its default.
5. Tick the box in `TODO.md`.

## Conventions

- **Idempotence is the contract.** These configs run on a schedule (see `k8s/`).
  Every mirror type must be safe to re-run against a populated destination. When
  you change sync behavior, think explicitly about run N, not just run 1: what
  accumulates, what goes stale, what gets deleted.
- **Don't regenerate upstream metadata.** For repo mirrors, mirror the metadata
  as-is rather than rebuilding it. See issue #34 for why `createrepo --update`
  was removed.
- **Destructive flags are opt-out, not implicit.** If a sync can delete files,
  it gets a config key and a README warning.
- Shell out with `sp.run(..., shell=True)` and f-strings, matching the existing
  style. There is no error handling or input validation yet (see `TODO.md`) —
  don't add a bespoke framework for one function.

## Testing

There is no unit test suite. Test by running the real thing in Docker:

```bash
docker build -t cattledrive:test .
docker run --rm -v $(pwd):/repo -v /path/to/dest:/path/to/dest \
  cattledrive:test cattleDrive /repo/config.local.yml
```

Mount each `dest` at its real host path so paths in the config resolve
identically inside the container.

- The `/regression-test` skill (`.claude/skills/regression-test/`) runs a config
  against `ghcr:latest` and a local build and compares the output.
- `utils/test-reposync-delete.sh` is an example of a self-contained test: stand
  up a throwaway upstream in a container, sync, mutate upstream, re-sync, assert.
  Prefer this shape over pointing tests at a public mirror — it's fast,
  offline, deterministic, and can test multi-run behavior.
- **Always verify a sync change across two runs.** A single run proves almost
  nothing about this tool.

Don't test by syncing a real distro repo. The reference `config.local.yml`
entries are multi-GB.

## Git and releases

- Branch per issue, named `issue-<number>`. PR into `main`.
- Images publish from a git tag: pushing `v*` triggers
  `.github/workflows/docker-image.yml`, which creates a GitHub release and
  pushes `ghcr.io/spartek-edge-labs/cattledrive`.
- Behavior changes that alter existing mirrors on their next run are **breaking**
  and need a major version bump. Call this out in the PR.
