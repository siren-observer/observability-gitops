# Observability GitOps repository

- Use signed commits and pull requests for every desired-state change.
- Never commit credentials or decrypted SOPS material.
- Pin images and OCI/Helm artifacts by digest.
- The production root is `clusters/re8ch`.

- Before using RE8CH self-service or platform tools, read [docs/RE8CH-TOOLS.md](docs/RE8CH-TOOLS.md) and inspect the current Re8ch model-callable tool list and schemas. Backend authorization or a workflow example does not prove plugin publication.
