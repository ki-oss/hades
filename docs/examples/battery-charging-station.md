
This example highlights some interesting differences between hades and the wonderful [simpy](https://simpy.readthedocs.io/en/latest/) based on their [Shared Resources example](https://simpy.readthedocs.io/en/latest/simpy_intro/shared_resources.html).

The key things to note are that the queue of waiting cars happens in a process rather than making use of a shared resource.

This means the state of the battery charging station contains some useful information (and the state can be interrogated after the simulation is run etc), but results in slightly less terse code and more logic within it.

```python
--8<-- "examples/battery_charging_station.py"
```

## Output

The output will look the same as in the simpy example but is arrived at in a different way!

```
Car 0 arriving at 0
Car 0 starting to charge at 0
Car 1 arriving at 2
Car 1 starting to charge at 2
Car 2 arriving at 4
Car 0 leaving the bcs at 5
Car 2 starting to charge at 5
Car 3 arriving at 6
Car 1 leaving the bcs at 7
Car 3 starting to charge at 7
Car 2 leaving the bcs at 10
Car 3 leaving the bcs at 12
```
