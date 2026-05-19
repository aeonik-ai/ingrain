# Hermes Integration

Aeonik Ingrain can integrate with Hermes in two modes.

## Sidecar Mode

Keep your current Hermes external memory provider, including OpenViking:

```bash
ingrain ingest hermes
ingrain compile
ingrain hydrate --query "what should I know before continuing this project?"
```

## Live Provider Mode

Install the user memory provider:

```bash
ingrain install hermes
hermes config set memory.provider ingrain
```

Hermes currently supports one external `memory.provider` at a time. If you use OpenViking today, live provider mode may replace it until Hermes supports provider chaining.

Ingrain stores provider data under `$HERMES_HOME/ingrain` by default. Set `INGRAIN_HOME` to override this.
