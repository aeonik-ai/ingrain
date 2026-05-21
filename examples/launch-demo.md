# End-to-end Demo: consolidate → hydrate → why

A 60-second walkthrough of the v0.2 path: record raw events, let the LLM consolidator turn them into cards, hydrate a fresh session, then audit *why* a card exists.

```bash
# 1. Fresh project
mkdir -p /tmp/ingrain-demo && cd /tmp/ingrain-demo
ingrain init

# 2. Stash a few learned-experience signals.
ingrain remember --type correction \
  "Do not push to main without running 'make test' first — the CI gate is downstream of merge."
ingrain remember --type decision \
  "Production database is Postgres 16, not SQLite. SQLite is only for unit-test fixtures."
ingrain remember --type project_fact \
  "Frontend lives in apps/web; the marketing site is a separate Next.js app in sites/marketing."

# 3. Run the LLM consolidator (uses `hermes -z`; no API keys).
ingrain consolidate

# 4. Hydrate the brief a future session would see.
ingrain hydrate --level brief --query "about to push a database migration to main"

# 5. Audit the source of any card that matches a query.
ingrain why "push to main"
```

**What you should see:**

- Step 4 returns a `<aeonik_ingrain_context>` block containing all three facts, with the `push to main` correction surfaced for the migration-style query.
- Step 5 shows the originating event id, the consolidator's confidence, the reason it became a card, and the timestamp — the audit trail that distinguishes Ingrain from generic memory layers.

For the auto-consolidate loop (no manual `ingrain consolidate` calls), install the Hermes plugin: `ingrain install hermes-plugin`. After a Hermes restart, every session ends with consolidation against the new events.
