# Examples

Every Wireme capability appears in at least one runnable example. Each file
is small, self-checking, and shows one idea in the preferred style. Run any
of them with:

```bash
uv run python examples/basic.py
```

## Capability index

| Capability                                     | Example                  |
| ---------------------------------------------- | ------------------------ |
| Direct and reusable dependencies               | `basic.py`               |
| Constructor and method injection               | `classes.py`             |
| Nested factories and per-call caching          | `nested.py`              |
| Class, instance, and method factories          | `factories.py`           |
| Process-wide singletons                        | `singletons.py`          |
| Generator and async resource cleanup           | `resources.py`           |
| Side-effect dependencies (`requires`) with injected context | `requires.py` |
| Wiring many methods with an apply combinator   | `method_wiring.py`       |
| Test overrides                                 | `overrides.py`           |
| Protocol-typed dependencies                    | `protocols.py`           |
| Explicit keyword values over injection         | `protocols.py`           |
| Building custom integrations                   | `custom_integration.py`  |
| FastAPI `FromWeb` with classes and aliases     | `fastapi_integration.py` |
| FastAPI request-scoped resources               | `fastapi_resources.py`   |
| FastAPI nested-safe web overrides              | `fastapi_overrides.py`   |
| FastAPI endpoints wired directly               | `fastapi_endpoints.py`   |

All examples run in CI. When a public capability is added, add or extend an
example and list it here.
