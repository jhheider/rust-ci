# rust-ci

[![Lint](https://github.com/jhheider/rust-ci/actions/workflows/lint.yml/badge.svg)](https://github.com/jhheider/rust-ci/actions/workflows/lint.yml)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Shared CI/CD for jhheider's Rust projects: reusable GitHub Actions **workflows**
and composite **actions**, so every repo runs the same fmt/clippy/test/audit/
release logic and improvements propagate from one place. Only the choices that
genuinely differ per repo (OS matrix, targets, whether it publishes crates) live
in each consumer's thin caller workflow.

Pin consumers to the `v1` tag. Breaking changes get a new major tag.

## Reusable workflows

### `ci.yml` - fmt + clippy + test (+ optional coverage)

No separate `cargo check` job: `cargo clippy --all-targets` with `-D warnings`
compiles everything check would, so a check job is only wasted minutes.

```yaml
name: CI
on:
  push:
    branches: [main]
    paths-ignore: ["**.md", "LICENSE*", ".gitignore"]
  pull_request:
    paths-ignore: ["**.md", "LICENSE*", ".gitignore"]
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  ci:
    uses: jhheider/rust-ci/.github/workflows/ci.yml@v1
    with:
      os: '["ubuntu-latest","macos-latest"]'   # default is 3-OS incl. windows
      coverage: true                            # default false
    secrets: inherit
```

Inputs: `os`, `toolchain` (default `stable`), `rustflags` (default `-D warnings`
- do not add `-A` escapes, fix the code), `clippy-args`, `test-args`, `coverage`.

### `audit.yml` - weekly cargo-audit

```yaml
name: Security Audit
on:
  schedule: [{ cron: "0 6 * * 1" }]   # Mondays 06:00 UTC
  workflow_dispatch: {}
jobs:
  audit:
    uses: jhheider/rust-ci/.github/workflows/audit.yml@v1
```

### `style.yml` - ASCII prose gate (no em/en-dashes)

```yaml
name: Style
on:
  pull_request:
  push: { branches: [main] }
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
jobs:
  style:
    uses: jhheider/rust-ci/.github/workflows/style.yml@v1
    with:
      skip-prefixes: "LICENSE fixtures/"   # default "LICENSE"
```

### `release.yml` - build, attach, optionally publish + bump tap

Wire it to `release: [published]`. Everything a repo does not need stays off.

The caller MUST grant `permissions: contents: write` - a reusable workflow
cannot request more permission than its caller holds. `targets` is a matrix
object (`{"include": [...]}`).

```yaml
name: Release
on:
  release: { types: [published] }
# Required: the reusable build job attaches assets to the release.
permissions:
  contents: write
jobs:
  release:
    uses: jhheider/rust-ci/.github/workflows/release.yml@v1
    with:
      bin-name: govee-tui
      targets: |
        {"include": [
          {"os":"ubuntu-latest","target":"x86_64-unknown-linux-musl","asset":"govee-tui-linux-x86_64.tar.gz"},
          {"os":"macos-latest","target":"x86_64-apple-darwin","asset":"govee-tui-macos-x86_64.tar.gz"},
          {"os":"macos-latest","target":"aarch64-apple-darwin","asset":"govee-tui-macos-aarch64.tar.gz"}
        ]}
      # gen-docs: true                 # binary supports --manpage/--completions
      # publish-crates: true
      # crates: "edikt-core edikt-syntax edikt"   # dependency order
      # tap-repo: jhheider/homebrew-tap
      # tap-formula: Formula/govee-tui.rb
    secrets: inherit
```

`musl` and non-native `aarch64-unknown-linux-gnu` targets auto-install their
toolchains from the target triple - no extra config.

## Composite actions

- `actions/setup-rust` - checkout + toolchain + shared build cache. Inputs:
  `toolchain`, `components`, `targets`, `cache`, `shared-key`.
- `actions/no-em-dash` - fail on em/en-dashes in tracked files (the logic behind
  `style.yml`; a companion script, not an inline heredoc).
- `actions/publish-crates` - publish crates in dependency order, skipping any
  version already on crates.io (unlike `katyo/publish-crates`, which aborts).
- `actions/bump-tap-formula` - retag URLs and recompute shas in a binary
  Homebrew formula, then push it to the tap.

Each workflow/action carries its own docstring; the reusable workflows are in
`.github/workflows/`, the composite actions in `actions/`. rust-ci lints itself
(`lint.yml`): actionlint over the workflows, `py_compile` over the scripts, and
its own `no-em-dash` action over its prose.
