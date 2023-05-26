# Tutorial

This is a stub for now, but will be expanded to expand on each of the constituent files.

## Data Models

::: ki_abv.framework.data_models.trivial.market
::: ki_abv.framework.data_models.trivial.world

## Events 

::: ki_abv.framework.events.trivial.market
::: ki_abv.framework.events.trivial.world

## World Processes
::: ki_abv.framework.process.trivial.world.catastrophe

## Market Processes

::: ki_abv.framework.process.trivial.market.brokers
::: ki_abv.framework.process.trivial.market.leads
::: ki_abv.framework.process.trivial.market.reinsurance
::: ki_abv.framework.process.trivial.market.follower


## The internals of a syndicate

::: ki_abv.framework.process.trivial.internal.syndicate_quote_monitor
::: ki_abv.framework.process.trivial.internal.claims
::: ki_abv.framework.process.trivial.internal.exposure_management


## Pulling it all together
```python
--8 < --"tests/framework/test_trivial_sim_event_queue.py"
```
## Visualising the simulation

--8<-- "docs/library/tests_snapshots/framework/snapshots/test_trivial_sim_event_queue/test_trivial_complete_insurance_sim_gives_expected_network_diagrams/trivial-complete-insurance-sim-instance-ack-diagram.md"
