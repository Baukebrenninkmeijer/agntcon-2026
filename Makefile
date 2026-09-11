.PHONY: sync-orq sync-orq-apply

# Safe default: show the semantic plan without mutating Orq.
sync-orq:
	uv run python scripts/sync_orq_resources.py

# Explicit mutation followed by a second, no-op verification pass.
sync-orq-apply:
	uv run python scripts/sync_orq_resources.py --apply

.PHONY: deck deck-local

# Public build: no licensed font, this is the tracked slides/pydata-2026.html.
deck:
	uv run python slides/build_deck.py

# Presenting build: embeds ES Klarheit Kurrent, writes the Git-ignored slides/pydata-2026.local.html.
deck-local:
	DECK_FONT_DIR=$${DECK_FONT_DIR:-$$HOME/.claude/skills/orq-chart-style/fonts} uv run python slides/build_deck.py
