# Validation — 2026-10-29

Current status: the initial hardening was committed and pushed by the owner at `e79cef3cd2b425139bc97b45c18abd1815753e26`. The CI follow-up below records the failed first remote attempt and the locally checked correction; the initial preparation results remain historical.


Prepared version: `1.1.0`. Starting commit: `96d10ad88714fe27afc1df9b700e2996a33fa4a6` plus the uncommitted hardening changes. Tests ran from temporary copies of the source on macOS arm64; the original project environments and personal Docker daemon were not modified.

| Check | Actual result |
| --- | --- |
| Environment | Python 3.12.16 et 3.13.18 |
| Quality gates | 78 tests unitaires par interpréteur ; couverture 92,29 % ; Ruff et mypy strict réussis ; 2 intégrations exclues |
| Focused regressions | Protection du nom de volume hexadécimal, normalisation des erreurs SDK, lecture bornée de politiques, UTF-8, symlinks/FIFO, profondeur YAML et durées hors plage |
| Runtime dependency audit | No known vulnerabilities reported by pip-audit for the locked runtime set, consulted on 2026-10-29; package identifiers only were sent to public advisory services. |
| Distributions | Wheel and sdist built; Twine metadata checks passed; wheel and independently rebuilt sdist installed and smoke-tested in separate fresh environments. |
| Isolation | AI smoke scans only a synthetic Dockerfile; Docker smoke checks version and synthetic policy validation without contacting Docker. |
| Workflows | Six workflow files across the three projects validated locally with actionlint 1.7.12; no remote run was triggered. |

## Remaining limits

Local success is not evidence of a new GitHub run. Ubuntu/Debian execution of this iteration remains pending. Docker integration tests are prepared for a dedicated disposable runner and were not executed against the owner's daemon. Real systemd/SSH/firewall behavior, concurrent Docker state changes, exhaustive vulnerability coverage and release publication are not established by these results.

The new package versions are prepared locally, not published. No Git staging, commit, push, tag or release was performed. Historical results remain historical in the existing project documents and Obsidian notes.

## CI follow-up — 2026-10-29

- Remote evidence: [CI run](https://github.com/Badis-M/docker-disk-guardian/actions/runs/40832114882) at `e79cef3cd2b425139bc97b45c18abd1815753e26`; inspected read-only, without rerunning a workflow.
- Observed result: Les jobs qualité Python 3.12/3.13 et sécurité ont réussi. Les deux tests d’intégration Docker ont réellement réussi sur le runner jetable (2 passed, 78 deselected). Le job package a échoué sur les mêmes options uv incompatibles.
- Correction: Retrait de `--no-build` et de l’option de build isolation inutile, en conservant `--only-binary :all:` et `--no-deps` pour installer le wheel.
- Local verification: Boucle exacte d’installation et de reconstruction extraite du workflow rejouée avec uv 0.13.6 et Python 3.12 : wheel et sdist reconstruite installés et smoke tests réussis, sans accès au Docker personnel. La commande GNU de génération des sommes, inchangée, n’a pas été rejouée sur macOS.
- Scope: only CI command compatibility or test-linter annotations changed. Runtime behavior, package versions, lock files and release authorization remain unchanged.
- Pending: the corrected revision has not run on GitHub. No commit, push, tag, release or workflow dispatch was performed by the agent during this follow-up.
