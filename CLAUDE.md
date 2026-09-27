# CLAUDE.md

Shared CI/CD for jhheider's Rust projects: reusable workflows in
`.github/workflows/` and composite actions in `actions/`, consumed from other
repos pinned at `@v1`. The README is the consumer-facing surface; when an
input, job or action changes, update both in the same commit.

House rules:

- Lint before you push: `pkgx actionlint` over every workflow you touch. The
  repo's own `lint.yml` gates PRs (actionlint, `py_compile` over the companion
  scripts, and the dogfooded `no-em-dash` action). Prose must stay free of
  em/en-dashes or the style job fails.
- Self-tests are dispatch-only harnesses (`_selftest-*`) that call the
  reusable workflows by local path (`./.github/workflows/...`). rust-ci has no
  Cargo project, so an expected failure after validation is the accepted shape;
  getting past startup is the point.
- Release by pushing a strict `vX.Y.Z` tag: `float-tags.yml` advances the `vX`
  and `vX.Y` floats forward only, which is how `@v1` callers receive changes.
- This is a public repo: no session-specific lines (no `Claude-Session:`, no
  claude.ai URLs) in any committed file. Commits keep
  `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
