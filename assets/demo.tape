# Aeonik Ingrain — VHS tape for the README demo GIF.
#
# Generates assets/demo.gif. Run with:
#   vhs assets/demo.tape
#
# Requirements:
#   - vhs (charmbracelet): brew install vhs
#   - aeonik-ingrain installed in the current environment (pipx is fine)
#   - A clean /tmp/ingrain-demo dir (the tape recreates it)
#
# The tape is paced for a ~40 second GIF that fits comfortably in a README
# without auto-playing past the viewer's attention. Edit Sleep values to
# adjust pace.

Output assets/demo.gif

Set FontSize 18
Set FontFamily "JetBrains Mono"
Set Width 1280
Set Height 720
Set Theme "Catppuccin Mocha"
Set Padding 20
Set TypingSpeed 50ms
Set PlaybackSpeed 1.0

# Hidden setup: reset the demo dir + cd into it.
Hide
Type "rm -rf /tmp/ingrain-demo && mkdir /tmp/ingrain-demo && cd /tmp/ingrain-demo && clear"
Enter
Sleep 500ms
Show

# 1. Initialize ──────────────────────────────────────────────────────────────
Type "# Set up a fresh learned-experience ledger"
Sleep 800ms
Enter
Type "ingrain init"
Sleep 300ms
Enter
Sleep 1500ms

# 2. Capture a real correction ───────────────────────────────────────────────
Type ""
Enter
Type "# Tell the agent something it should remember next time"
Sleep 800ms
Enter
Type "ingrain remember --type correction 'Do not push to main without running tests first.'"
Sleep 300ms
Enter
Sleep 1500ms

# 3. Capture a project fact ──────────────────────────────────────────────────
Type "ingrain remember --type project_fact 'Production database is Postgres, not SQLite.'"
Sleep 300ms
Enter
Sleep 1500ms

# 4. Consolidate via Hermes (no API key) ─────────────────────────────────────
Type ""
Enter
Type "# Consolidate using Hermes's own model — no external API key"
Sleep 800ms
Enter
Type "ingrain consolidate --limit 20"
Sleep 300ms
Enter
Sleep 8000ms

# 5. Show what the agent sees at the start of the next session ──────────────
Type ""
Enter
Type "# What the next agent session will see"
Sleep 800ms
Enter
Type "ingrain hydrate --query 'about to push'"
Sleep 300ms
Enter
Sleep 3000ms

# 6. The audit trail — the differentiator ───────────────────────────────────
Type ""
Enter
Type "# Why does the agent believe this? The audit trail."
Sleep 800ms
Enter
Type "ingrain why 'push'"
Sleep 300ms
Enter
Sleep 4000ms

# 7. Closing pause ──────────────────────────────────────────────────────────
Type ""
Enter
Type "# That's it. One install, no API keys, full provenance."
Sleep 800ms
Enter
Sleep 3000ms
