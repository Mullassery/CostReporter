# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Architecture

ClaudeBeacon is a **Rust + Python hybrid** optimized for performance with Python flexibility:

### Layer 1: Rust Core (`crates/beacon-core/`)
**High-performance memory, observability, and audit system**

- `memory.rs` — Persistent project context storage
- `observability.rs` — Tool call tracking and analytics
- `audit.rs` — Immutable audit logs for compliance
- `storage.rs` — SQLite/PostgreSQL connection pool
- `mcp.rs` — MCP protocol handler

**Why Rust:**
- ✅ Fast (~100x faster than pure Python for I/O)
- ✅ Memory-efficient (critical for observability data)
- ✅ Safe concurrency (for multi-session handling)

### Layer 2: Python Wrapper (`python/`)
**Native Python API with PyO3 bindings**

- `python/src/lib.rs` — PyO3 FFI wrapping Rust core
- `python/src/__init__.py` — High-level Pythonic API

**Why Python wrapper:**
- ✅ Integrate with pandas, SQLAlchemy, FastAPI
- ✅ Natural Python ecosystem (logging, testing, deployment)
- ✅ Easier to extend with Python libraries

### Communication Flow

```
Claude Code
     ↓
TypeScript Skill (future)
     ↓
Python API (claude_beacon.Beacon)
     ↓
Rust Core (_core.Beacon) [PyO3 extension]
     ↓
SQLite/PostgreSQL
```

## Build & Test Commands

**Install dependencies:**
```bash
make install
```

**Build Rust + Python:**
```bash
make build          # Full build
maturin develop     # Dev install (hot reload)
maturin build --release  # Release wheel
```

**Tests:**
```bash
cargo test --workspace --release    # Rust tests
pytest tests/ -v                    # Python tests
pytest --cov=tests                  # With coverage
```

**Format & lint:**
```bash
make fmt
make lint
```

## Project Structure

```
ClaudeBeacon/
├── Cargo.toml                       # Workspace root
├── crates/
│   └── beacon-core/                # Rust core (high-performance)
│       ├── Cargo.toml
│       └── src/
│           ├── lib.rs              # Entry point
│           ├── memory.rs           # Context persistence
│           ├── observability.rs    # Tool tracking
│           ├── audit.rs            # Compliance logs
│           ├── storage.rs          # DB backend
│           └── mcp.rs              # Protocol handler
│
├── pyproject.toml                   # Python package config
├── python/
│   └── src/
│       ├── lib.rs                  # PyO3 bindings
│       └── __init__.py             # Python API
│
├── tests/                           # Tests (both Rust + Python)
├── CLAUDE.md                        # This file
└── Makefile                         # Dev tasks
```

## Important Implementation Details

### Memory System
- Stores context in SQLite (default: `~/.claude/beacondb/memory.sqlite`)
- Serializes to JSON for compatibility
- Summarizes to avoid token waste
- Session-aware (multiple parallel sessions supported)

### Observability
- Zero-copy logging (Rust performance)
- Tracks: tool calls, arguments, responses, latency, tokens
- Aggregates: error rates, slowest operations, token distribution
- Real-time queries via Python API

### Audit Logging
- Immutable append-only (cannot be deleted)
- HIPAA/SOC2 compliant (configurable retention)
- Encrypted at rest (optional)
- Export to PDF/JSON/CSV

### Storage Backends
- **SQLite** (default, local, zero-config)
- **PostgreSQL** (production, multi-user, replication)
- Configurable via connection string

## Build Constraints

### PyO3 Runtime
- `tokio::runtime::Runtime` required for async Rust in Python
- `block_on()` converts async to sync at FFI boundary
- Python GIL released during Rust execution

### Memory Safety
- Rust ownership model prevents memory leaks
- Python ownership via PyO3 reference counting
- No unsafe code (preferred)

## Common Tasks

**Add a new metric to observability:**
1. Add field to `ObservabilityTracker` struct
2. Update `get_summary()` to include new metric
3. Update Python wrapper in `__init__.py`
4. Test with `pytest tests/test_observability.py`

**Add database schema:**
1. Create migration in `crates/beacon-core/migrations/`
2. Update `StorageBackend` to handle new schema
3. Rebuild with `maturin develop`

**Deploy Python package:**
```bash
maturin build --release
twine upload dist/*.whl
```
