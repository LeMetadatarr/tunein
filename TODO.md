# TODO — tunein

## Open issues

- [ ] #11 Dependency Dashboard (Renovate bot meta-issue)

## Gaps

- [ ] `pyproject.toml` `Homepage` points to `https://github.com/OpenJarbas/tunein`; update to the canonical `TigreGotico/tunein`.
- [ ] `.coverage` artifact is committed despite being in `.gitignore`; remove from tracking.
- [ ] `tunein.egg-info/` is committed despite `*.egg-info/` being in `.gitignore`; remove from tracking.
- [ ] No `skill-check`/`opm-check` workflow — not applicable (this is a library, not an OVOS plugin/skill). No action needed; noted for completeness.
- [ ] No typecheck config (mypy/pyright) wired in, though `.mypy_cache` is gitignored; consider adding if type coverage is desired.

CI is otherwise complete: `build-tests`, `coverage`, `license_check`, `lint`, `release_workflow`, `publish_stable`, `release-preview`, `repo-health`, `pip_audit`, `conventional-label`, plus a custom `nightly-live` cassette-drift detector. Tests exist (unit + VCR), README and pyproject present.

## Code TODOs

None found. (No TODO/FIXME/XXX/HACK markers in `tunein/` or `test/` source; the only matches are the Portuguese word "Todos" inside VCR cassette fixtures.)
