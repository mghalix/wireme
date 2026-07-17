# Wireme guide

One page per concept, in reading order. Every page ends with a runnable
example from [examples/](https://github.com/mghalix/wireme/blob/main/examples/README.md).
Throughout the guide, Wireme resolves dependencies and leaves every value
unchanged.

1. [Getting started](getting-started.md) - install, wire a function, reuse a dependency
2. [Wiring classes](classes.md) - constructor and method injection
3. [The dependency graph](dependency-graph.md) - nesting, caching, singletons
4. [Resources](resources.md) - async factories and generator cleanup
5. [Testing](testing.md) - overrides and explicit values
6. [Side-effect dependencies](side-effects.md) - guards and auditing with requires
7. [Protocol dependencies](protocols.md) - depend on interfaces
8. [FastAPI integration](fastapi.md) - FromWeb, resources, web overrides
9. [Building integrations](extending.md) - Wireme as your project's DI primitive

Architecture decisions live in [docs/adr](https://github.com/mghalix/wireme/blob/main/docs/adr/README.md).
