# Validation control

## Constraints without models

`@wire` validates every annotated parameter through pydantic, so one
constrained parameter needs neither a `BaseModel` nor a `TypeAdapter`: put
the constraint in the signature with `Annotated`, preferably behind a
`type` alias so it is reusable and strictly typed:

```python
from pydantic import AfterValidator, Field

type Limit = Annotated[int, Field(gt=0, le=100)]
type Username = Annotated[str, Field(min_length=2, max_length=32)]


def normalize(value: str) -> str:
    return value.strip().lower()


type NormalizedUsername = Annotated[Username, AfterValidator(normalize)]


@wire
def search_users(query: Username, limit: Limit = 20) -> str:
    ...
```

Invalid input raises `ValidationError`; valid input is coerced to the
annotated type. Every pydantic annotation works: `Field` constraints,
pydantic types such as `PositiveInt`, and custom validators. Factory
parameters are validated the same way, so constraints travel with the
dependency graph.

## Turning validation off

`@wire` validates arguments and the return value with pydantic. Turn either
off per function when a hot path does not need it:

```python
@wire(cast=False, cast_result=False)
def operation(value: int) -> int:
    ...
```

`wired()` accepts the same `cast` and `cast_result` flags per declaration.

## Project-wide defaults

The configured form of `wire` returns a reusable decorator. To apply your
preferred options everywhere, bind them once in a project module and import
that binding instead of `wireme.wire`:

```python
# myapp/di.py
import wireme

wire = wireme.wire(cast=False, cast_result=False)
```

```python
# everywhere else
from myapp.di import wire
```

The binding works on functions, methods, and classes. There is no
process-global configuration by design: a bound decorator is explicit,
import-order safe, and cannot change the behavior of libraries that use
Wireme themselves. At call sites that need different options, use the full
`wireme.wire(...)` form.

## Errors

Wireme exposes:

```python
from wireme import ValidationError, WiremeError
```

- `WiremeError` is the base error exposed by Wireme.
- `ValidationError` represents dependency input or result validation
  failures.

Project-specific DI errors may inherit from `WiremeError`.

## Runnable examples

[examples/field_constraints.py](https://github.com/mghalix/wireme/blob/main/examples/field_constraints.py),
[examples/validation.py](https://github.com/mghalix/wireme/blob/main/examples/validation.py)

Next: [Protocol dependencies](protocols.md)
