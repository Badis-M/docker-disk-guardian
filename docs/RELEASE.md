# Validation and release procedure

Prepared version: `1.1.0`. No tag or release was created by the 2026-10-29 preparation.

## CI contract

Pull requests and pushes to `main` run `.github/workflows/ci.yml`. The same workflow is reusable by the manual release workflow, with the requested tag as its checkout reference.
Actions use verified immutable SHAs. Repository access is read-only during validation, checkout credentials are not persisted, and job timeouts are explicit.

The first remote attempt and its corrective follow-up are recorded in `VALIDATION.md`. A successful remote run of the corrected revision is still required before release. Branch protection rules are managed separately; a workflow file alone does not make checks mandatory for merging.

## Release authorization

1. Review the changes and validation results, commit and push only with the owner's authorization.
2. Choose the next version and check the changelog and version constants. Never move an existing tag.
3. With separate explicit authorization, create and push the matching stable `vX.Y.Z` tag on a commit reachable from `main`.
4. With explicit publication authorization, start the **Release** workflow manually and enter that existing tag. A normal push does not publish a release.
5. The reusable CI validates the selected revision and uploads its tested distributions. A failed check blocks publication.
6. The publication job verifies exact tag/HEAD identity, version agreement, main ancestry and checksums. It downloads the artifacts of this same run instead of rebuilding for publication.
7. Only the publication job receives `contents: write`; its `GH_TOKEN` is the ephemeral workflow token. No permanent token, PyPI account or deployment service is required.

`python3 scripts/check_release.py vX.Y.Z` is a read-only release check, requiring a full checkout with tags and `origin/main`. It intentionally rejects historical tags whose version differs from the current source.
GitHub environment approval rules may be added separately if the repository's plan supports them. The current manual dispatch requires an operator action; it is not a second-reviewer approval gate.

## Recovery and maintenance

If validation fails, fix the source and prepare a new reviewed revision. Do not bypass failing tests or replace a published tag. A failed publication can be investigated without rerunning destructive operations on personal resources.
Review pinned actions, image digests, dependency locks and security advisories when updating dependencies. A passing dependency audit means no known advisory was reported at that time, not proof of absence of vulnerabilities.

## Python distributions

Use uv `0.13.6`; `uv.lock` pins the resolved runtime, development, build and security dependencies. Package metadata keeps compatible runtime ranges for consumers. Contributor environments are prepared with `uv sync --locked --extra dev --group build --group security --python 3.12`.

- `make check coverage`: formatting, lint, strict typing, tests and an 80% coverage floor.
- `make audit`: exports only locked runtime dependencies, then consults public vulnerability metadata. This requires network access; it sends package identifiers, not repository source.
- `make build`: builds wheel and sdist without build isolation using the locked build group, then runs `twine check`.
- CI installs locked runtime dependencies with hashes in fresh environments, installs the wheel without dependency resolution, rebuilds the sdist and smoke-tests that installed package independently of `src/`.
- Uploaded distributions include `SHA256SUMS`. Build outputs, reports, environments and `contexte.md` are excluded from source control.

To update dependencies deliberately, use `uv lock --upgrade`, inspect the changes and rerun the matrix, audit and distribution checks. Do not refresh the lock during an ordinary `--locked` CI run.

Docker integration is a required CI job on an ephemeral GitHub runner, using a BusyBox digest prepared by a dedicated pull step. The tests themselves never auto-pull or call global prune. They remove only their own UUID resources and check default protection and explicitly opted-in targeted volume deletion.
Wheel and sdist metadata deliberately use Core Metadata 2.4 because the locked Twine 6 validator rejects metadata 2.5. This is a build compatibility choice, not a runtime dependency.
