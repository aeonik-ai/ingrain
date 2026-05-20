# Publishing

The package name is `aeonik-ingrain`.

The CLI command is `ingrain`.

Do not publish as `ingrain`: that name is already occupied on PyPI by another project.

## Before PyPI

Use the GitHub install path:

```bash
pipx install "git+https://github.com/aeonik-ai/ingrain.git"
```

## PyPI Release

Recommended release path:

```bash
python3 -m pip install build twine
python3 -m build
python3 -m twine check dist/*
python3 -m twine upload dist/*
```

After publish, the README quick-start can use:

```bash
pipx install aeonik-ingrain
```

## Smoke Test

Use a clean environment:

```bash
python3 -m venv /tmp/ingrain-publish-smoke
/tmp/ingrain-publish-smoke/bin/python -m pip install aeonik-ingrain
/tmp/ingrain-publish-smoke/bin/ingrain --version
/tmp/ingrain-publish-smoke/bin/ingrain eval
/tmp/ingrain-publish-smoke/bin/ingrain les-hard --output-dir /tmp/ingrain-les-hard
/tmp/ingrain-publish-smoke/bin/ingrain skill show codex
```

Expected result:

```text
Aeonik Ingrain LES-Core Smoke Eval
Learned Experience Score
Total                           100/100
```

Only use this as a local regression-gate screenshot. Do not frame it as an external benchmark, provider leaderboard, or proof that Ingrain beats Hindsight/OpenViking.

For a stronger launch artifact, use LES-Hard:

```text
Ingrain                         542/560
```

Label it exactly as LES-Hard v0, an Ingrain self-eval. Do not present it as a provider comparison.

## GitHub Release Checklist

- Tag `v0.1.0`.
- Attach the eval report.
- Mention that the project is local-first and has no network or LLM dependency by default.
- Mention CLI + Skill + PRACTICE.md as the default adoption path.
- Link LES-Hard v0 results and raw artifacts.
- Mention that OpenViking live provider chaining is roadmap, not v0.
- Link the architecture graphic: `assets/ingrain-architecture.svg`.
