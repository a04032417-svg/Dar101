# Dar Template Factory — builder (branch `fx`)

Claude's half of Dar's template factory. Dar's AI teams design each product as a spec (`SPEC.md`); this branch holds the
builder that turns a spec into the 15-language Excel workbooks, checks every formula, renders the listing pictures and
encrypts the buyer's ZIP for Dar (`engine/`), the run's own steps (`runtime/fx.py`), and `fx/manifest.json`, which Dar reads.
Only items not yet taken in by Dar are kept here; the branch is one commit, rewritten on each run.
