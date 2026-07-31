# Changelog

## 0.2.0

- **Breaking:** the server moved every business endpoint from `/api/v1/...`
  to `/builder/v1/...` (see `edutap.pass_builder.app.API_PREFIX`). This
  client now sends requests to `/builder/v1/passes`,
  `/builder/v1/passes/{pass_id}`, `/builder/v1/passes/{pass_id}/save-link`
  and `/builder/v1/passes/preview` instead of the old `/api/v1/...` paths.
  The new path prefix is exposed as `edutap.pass_builder_api.API_PREFIX`.
- The deployment mount point in front of the business path (e.g.
  `/internal-api/wallet`) was never part of these request paths — it
  belongs in `base_url` and is unaffected by this change.
- A 0.2.x client requires a server that already carries the new
  `/builder/v1` convention; it will 404 against a server still serving
  `/api/v1`. Likewise, a pre-0.2 client will 404 against a server that has
  moved to `/builder/v1`. Upgrade the client and the server together.

## 0.1.0 (unreleased)

- Initial release: async client over the `edutap.pass_builder` REST
  service — pass creation/update, save-link generation, and preview
  rendering for Apple and Google wallets.
