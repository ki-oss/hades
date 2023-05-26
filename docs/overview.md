# Hades Overview

HADES (HADES Asynchronous Discrete Event Simulation) is a fairly simple framework for creating discrete event based simulation with static events and broadcasting. In general,
designed with a particular focus on the needs of simulation/validation of algorithmic underwriting strategies at Ki Insurance.

The core concepts are:

## Hades

::: ki_abv.framework.hades.hades
    options:
        heading_level: 4
## Event
`Event`s in `Hades` are immutable `pydantic` models including some `t` value - the time-step in the simulation when the event occurs, and data or identifiers relating to the event.

Events in `Hades` are static meaning that they are do not contain logic relating to the event as with some other DES frameworks. See [design justification](./design-justification.md) for why!

::: ki_abv.framework.hades.event
    options:
        heading_level: 4
## Process

::: ki_abv.framework.hades.process
    options:
        show_root_heading: true
        heading_level: 4


## Time 

::: ki_abv.framework.hades.time
    options:
        show_root_heading: true
        heading_level: 4
        
::: ki_abv.framework.hades.time.event
    options:
        show_root_heading: true
        heading_level: 4

::: ki_abv.framework.hades.time.day_steps
    options:
        show_root_heading: true
        heading_level: 4
::: ki_abv.framework.hades.time.process
    options:
        show_root_heading: true
        heading_level: 4
::: ki_abv.framework.hades.time.logging
    options:
        show_root_heading: true
        heading_level: 4
