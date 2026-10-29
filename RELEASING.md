# Release candidates

Nexus does not currently publish a package or container. The package metadata
still uses the upstream distribution name `stride-gpt`; that name and the
upstream Docker Hub image belong to their respective owners. Do not publish this
fork to those namespaces without authorization.

A version tag triggers the [release candidate workflow](.github/workflows/release.yml).
It checks that the tag matches `pyproject.toml`, builds a wheel and source
archive, and uploads them as workflow artifacts. It does **not** publish to
PyPI, push an image, or create a GitHub Release. A manual run builds the same
artifacts without requiring a tag. Normal PR checks, the clean wheel audit, and
security checks should pass before a tag is created.

Before enabling a future release, choose and verify Nexus-controlled package and
container names, update package metadata and installation documentation, set up
OIDC trusted publishing and protected deployment environments, and add reviewed
publish jobs with appropriate tests, provenance and least-privilege permissions.
Preserve upstream attribution and licence notices. Publishing is deliberately
unconfigured until these decisions are made.
