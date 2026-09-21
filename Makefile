.PHONY: sync-orq sync-orq-apply

# Safe default: show the semantic plan without mutating Orq.
sync-orq:
	uv run python scripts/sync_orq_resources.py

# Explicit mutation followed by a second, no-op verification pass.
sync-orq-apply:
	uv run python scripts/sync_orq_resources.py --apply

.PHONY: deck

# Build slides/pydata-2026.html with the embedded typeface.
deck:
	uv run python slides/build_deck.py

.PHONY: hooks

# Point Git at the tracked hooks; run once per clone or worktree.
hooks:
	git config core.hooksPath .githooks
