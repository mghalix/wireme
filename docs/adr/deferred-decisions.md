# Deferred decisions

Open questions that do not need an answer yet. Each entry names the
question, why it is deferred, and what evidence would force a decision.
When one is decided, it becomes an ADR and the entry is removed.

- Runtime enforcement of keyword-only injected parameters (ADR 0009 keeps
  it a documentation convention). Decide if users keep hitting the silent
  positional drop despite the `*` convention; the cost is per-call argument
  binding or a decoration-time warning.
- Rejecting or warning on positional values aimed at injected parameters
  (ADR 0002). Same trigger and cost profile as the entry above; upstream
  may also fix the argument mapping, which would moot it.
- Dataclass field injection: `@wire` above `@dataclass` with wired field
  defaults (ADR 0010 wires only explicit `__init__`). Decide when a real
  user asks; the open questions are generated-signature handling and field
  default semantics.
- Per-entry configuration for `requires` factories, for example disabling
  the cache of one guard (ADR 0013 ships plain callables with defaults).
  Decide when a guard needs non-default settings in practice.
- Request-scoped or instance-scoped providers (ADR 0003 keeps one
  process-level provider). Decide if a user needs per-tenant graphs or
  parallel in-process test isolation.
- Additional framework integrations under `wireme.<framework>` (ADR 0004
  sets the packaging pattern). Decide per framework on demand.
- A raising Wired() placeholder: Wired() returns Ellipsis today, so a
  factory called directly outside resolution receives `...` and fails later
  with an unrelated error, or not at all for generator factories. A
  sentinel that raises an actionable error on any use would fail fast at
  the misuse site. Decide if direct-call confusion recurs; the cost is a
  carefully behaved sentinel (repr, equality, framework edge cases).
