# Visualisation

Hades largely leaves visualisation up to the user. However it does provide some batteries for a few different options.

1. Visualising using recorded events and event results from the `Hades` instance (useful for building graphs of events and simulation level visualisation).
1. Visualising using the state of a process (useful for `matplotlib` / notebook rendering of individual processes).
1. Visualising live using a process or a subclass of `Hades` like `HadesWS`. (useful for live rendering of long running simulations)

## Visualising using Hades recorded events

Hades can record events and their results. See [`hades.event_results` and `hades.event_history`](api_reference/hades/#hades.core.hades.Hades.__init__).

This can be used to reconstruct a simulation as it happened or visualise the structure of the simulation itself based on responses.

??? "Tests demonstrating networkx DiGraph creation and mermaid rendering based on recorded events"
    ```python
    --8<-- "tests/visualisation/test_networkx.py"
    ```

## Visualising using the state of a process

Processes can be inspected after (or during a simulation) and used for visualisation. [Boids Example](./examples/boids.md#)

An example of visualisation using process state can be seen in the [boids example history collector process](./examples/boids/#history-collector-and-renderer).


## Visualising live interactions

Processes can also be set up to asynchronously share events to clients for custom frontends. See the [`WebSocketProcess`](./api_reference/visualisation/#hades.visualisation.websockets.WebSocketProcess).

Alternatively, `Hades` can be sub-classed to act as a server. This way all events and their results can be output to clients as they happen. See [`HadesWS`](./api_reference/visualisation/#hades.visualisation.websockets.HadesWS)

This style of visualisation is demonstrated in the [boids example too](http://localhost:8000/examples/boids/#results)
