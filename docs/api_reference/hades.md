
## Event Loop

The most important part of Hades is its core event loop.

Here is how it works.

``` mermaid
graph TB
    G[Getting Events for Next Timestep]
    I[Broadcast Events asynchronously to all registered Processes]
    K[Take top event from t Priority Queue]
    L[Move self.t to event.t]
    M[Collect all events at time self.t from priority queue]
    Z[End Simulation]
    N[Processes maybe add more events to the priority queue]
    O[Handle event results]


    G --> K
    K --> | event.t >  current simulation time | L
    L --> M
    K --> | event.t ==  current simulation time | M
    K --> | no event on queue | Z
    M --> | self.t > specified run until time | Z
    M --> I
    I --> N
    N --> O
    O --> G
```

!!! important
    Events can never be added in the past but they can be added for the current timestep

## Module

::: hades.core.hades
        
## Other points of note

* Exceptions are handled by raising the last one to occur within a timestep. If there are multiple they are simply logged at `ERROR` level
* Events at the same `t` are prioritised in the order they were added to the queue, however this shouldn't make too much difference in most cases as they will be executed as part of the same `asyncio.gather` regardless.
