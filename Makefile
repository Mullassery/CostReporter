.PHONY: install build test lint fmt clean run help setup-hooks

help:
	@echo "ClaudeBeacon development tasks (Rust + Python):"
	@echo "  make install         Install dependencies"
	@echo "  make build           Build Rust core + Python wrapper"
	@echo "  make dev             Dev install with hot reload (maturin)"
	@echo "  make test            Run all tests (Rust + Python)"
	@echo "  make test-rust       Rust tests only"
	@echo "  make test-python     Python tests only"
	@echo "  make lint            Lint Rust + Python"
	@echo "  make fmt             Format code"
	@echo "  make fmt-check       Check format"
	@echo "  make clean           Remove build artifacts"

install: setup-hooks
	@echo "Installing Rust dependencies..."
	rustup update
	@echo "Installing Python dependencies..."
	pip install maturin pytest pytest-cov black ruff mypy
	@echo "✓ Dependencies installed"

setup-hooks:
	@command -v pre-commit >/dev/null 2>&1 || pip install pre-commit
	pre-commit install

build:
	@echo "Building Rust core + Python wrapper..."
	maturin build --release
	@echo "✓ Build complete (wheels in target/wheels/)"

dev:
	@echo "Dev install (hot reload)..."
	maturin develop

test:
	@echo "Running Rust tests..."
	cargo test --workspace --release
	@echo "Running Python tests..."
	pytest tests/ -v --cov=tests
	@echo "✓ All tests passed"

test-rust:
	cargo test --workspace --release

test-python:
	pytest tests/ -v --cov=tests

lint:
	@echo "Linting Rust..."
	cargo clippy --workspace --all-targets
	@echo "Linting Python..."
	black --check python/ && ruff check python/ && mypy python/
	@echo "✓ Lint complete"

fmt:
	@echo "Formatting Rust..."
	cargo fmt --all
	@echo "Formatting Python..."
	black python/ && ruff check python/ --fix
	@echo "✓ Format complete"

fmt-check:
	cargo fmt --all -- --check
	black --check python/

clean:
	cargo clean
	rm -rf target dist build *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	@echo "✓ Clean complete"
