`Event`s in `Hades` are immutable `pydantic` models including some `t` value - the time-step in the simulation when the event occurs, and data or identifiers relating to the event.

Events in `Hades` are static meaning that they are do not contain logic relating to the event as with some other DES frameworks. See [design justification](../design-justification.md) for why!

::: hades.core.event
