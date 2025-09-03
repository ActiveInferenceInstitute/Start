PY=uv run python

.PHONY: help setup test lint format clone

help:
	@echo "Targets: setup, test, lint, format, clone URL=... DEST=... BRANCH=..."
	@echo "Also: clone-cognitive, clone-rxinfer, clone-activeinference, clone-pymdp"

setup:
	uv sync --all-extras --dev

test:
	uv run pytest -q --maxfail=1 --disable-warnings

lint:
	uv run ruff check ..

format:
	uv run black ..

clone:
	uv run python repos/clone_repo.py --url "$(URL)" --dest "$(DEST)" $(if $(BRANCH),--branch $(BRANCH),) --shallow

clone-cognitive:
	uv run python repos/clone_repo.py --url https://github.com/ActiveInferenceInstitute/cognitive --dest _clones/cognitive --shallow

clone-rxinfer:
	uv run python repos/clone_repo.py --url https://github.com/docxology/RxInferExamples.jl --dest _clones/RxInferExamples.jl --shallow

clone-activeinference:
	uv run python repos/clone_repo.py --url https://github.com/docxology/ActiveInference.jl --dest _clones/ActiveInference.jl --branch textbook --shallow

clone-pymdp:
	uv run python repos/clone_repo.py --url https://github.com/docxology/pymdp --dest _clones/pymdp --branch textbook --shallow

