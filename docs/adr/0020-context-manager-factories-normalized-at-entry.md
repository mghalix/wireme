# ADR 0020: Context manager factories are normalized at entry

- Status: Accepted
- Date: 2026-08-01

## Context

`@contextmanager` and `@asynccontextmanager` are the ordinary way to write a
resource in Python, and most real dependencies (database sessions, clients,
transactions) already exist in that form. FastDepends understands generator
and async-generator factories, but a decorated factory returns a context
manager object instead of yielding the dependency, so it was injected
unentered and never cleaned up.

`inspect.unwrap()` resolves the decorated form, but it follows every
`__wrapped__` chain, so it also strips unrelated decorators applied with
`functools.wraps`, including `functools.lru_cache`. Applying it only in
`wired()` also splits identity: the dependency registers under the wrapped
generator function while `override_dependency()` and
`override_web_dependency()` still key on the decorator helper, so overrides
silently do nothing.

## Decision

One private `_normalize_factory()` recognizes the two `contextlib`
decorators by the code object their helper closures share, and returns the
generator function the helper wraps. Anything else is returned untouched.

Normalization runs wherever a factory enters Wireme: `wired()`,
`override_dependency()` (both factories), and the bridged-adapter lookup in
`get_override_pairs()`. Declaration and override sites therefore agree on
one identity per dependency. In `get_override_pairs()` the direct FastAPI
pair keeps the callables as given, because a plain FastAPI dependency is
registered under the object passed to `Depends()`.

`wired()` gains overloads for `AbstractContextManager[R]` and
`AbstractAsyncContextManager[R]` so a decorated factory infers `R`, matching
the generator overloads.

## Consequences

- Positive: context managers behave exactly like the generator functions
  they wrap, including cleanup order, caching, FastAPI request lifecycle,
  and both override entry points.
- Positive: unrelated `functools.wraps` decorators and caches keep working,
  which unconditional unwrapping broke.
- Negative: detection depends on the closure shape of `contextlib`'s two
  decorators. This is stdlib behavior stable across supported Python
  versions and is regression tested; a change there degrades to injecting
  the unentered manager rather than misfiring on other callables.
- Neutral: third-party context manager decorators are not recognized. Pass
  the underlying generator function, or wrap it in one.
