.PHONY: sync-orq sync-orq-apply

# Safe default: show the semantic plan without mutating Orq.
sync-orq:
	uv run python scripts/sync_orq_resources.py

# Explicit mutation followed by a second, no-op verification pass.
sync-orq-apply:
	uv run python scripts/sync_orq_resources.py --apply
