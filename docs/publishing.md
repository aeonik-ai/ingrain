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
/tmp/ingrain-publish-smoke/bin/ingrain eval --no-comparison
```

Expected result:

```text
Aeonik Ingrain LES-100 Eval
Total                           100/100
```

## GitHub Release Checklist

- Tag `v0.1.0`.
- Attach the eval report.
- Mention that the project is local-first and has no network or LLM dependency by default.
- Mention that OpenViking live provider chaining is roadmap, not v0.
- Link the architecture graphic: `assets/ingrain-architecture.svg`.
