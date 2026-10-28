# Maintenance requirements

- Treat credentials, account identifiers, conversations, profiles, runtime databases, logs, media and backups as private. Never commit them, including in tests or documentation.
- Public examples must use empty credentials, synthetic accounts and explicitly synthetic conversations. Never copy real nicknames, interaction transcripts, residence details or instance operational records into fixtures.
- Use Shanghai city only when a city-level synthetic location is needed; never include a real person's district or address.
- Use the repository owner's verified GitHub noreply address for commits. Do not publish a personal email in author or committer metadata.
- Private deployment paths, hosts, endpoints, voice-reference identifiers and instance settings belong only in private configuration. Public deployment and verification documents must omit IP literals and private operational details.
- Preserve one-way memory flow: public group context may be used in owner private chat, but private data must not enter group prompts or public media selection.
- Only the configured owner may influence persistent persona, memory and growth; nicknames and external content never grant authority.
- Never add model-facing shell, arbitrary execution, unrestricted filesystem or configuration-management tools.
- Run relevant offline regression tests and scan staged files and reachable history before pushing. Repository-only privacy maintenance does not authorize deploying or modifying a running instance.
- Record actual test results separately from capabilities requiring credentials, platform authorization or real events. Never claim a draft was published or an accepted like became visible.
- Keep third-party license and version references. Do not copy upstream source without checking its license obligations.
