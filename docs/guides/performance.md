With a lot of simulations, performance will be a core concern. Hades is built with performance in mind but with a primary focus on IO-bound workloads rather than CPU-bound ones.

Hades runs on a single thread, but using `asyncio`, event notifications happen concurrently.

This means that depending on what the `notify()` method does on the processes within the simulation, it may be far quicker than a multi-processing approach using all of your CPU cores, or a bit slower than running synchronously.

Let's take two examples

## CPU Bound

As you might notice in the following example, none of the methods called when a `Boid` process (from the [boids example](../../examples/boids)) reacts to a `BoidMoved` event, are `async` flavoured.

```python
--8<-- "examples/boids/boids.py:210:236"
```

This means that we will get no speed up from running them concurrently in an `asyncio.gather`. An approach utilising multiple CPU cores or at least not slowing stuff down by creating coroutines etc may be faster here. 

However, CPU bound tasks may still benefit from the Hades approach. After all there is a limit to the number of cores likely to be present on a physical machine vs. on any machine over the network!

We could, for example, implement an API endpoint which takes the `BoidMoved` event over HTTP and does all the processing to return another event. We could then scale to millions of Boids being handled in a reasonable time frame!


## IO Bound

IO Bound tasks are Hades' bread and butter. When there are multiple IO-bound things being done through `asyncio` by separate processes during a timestep, or even by the same process, but in response to a different event, they will all be done concurrently before moving to the next timestep.

!!! note
    Concurrent handling of events within the same process does have some things to be careful of (see [process](../../api_reference/process/))

```python
--8<-- "examples/multi_agent_llm_storytelling/processes.py:127:162"
```

## Optimising for Performance

Apart from ensuring you are taking advantage of `async` implementations for IO bound tasks within processes (e.g. `httpx` instead of `requests`), there are a number of other performance optimisations you can make in terms of configuring `Hades`.

These arguments are detailed in [Hades](../../api_reference/hades#hades.core.hades.Hades), and mostly involve removing some non-essential functionality to give better performance.

These are used to speed things up in the boids example.
```python
--8<-- "examples/boids/boids.py:372:374"
```
