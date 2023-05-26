# Visualisation

Hades largely leaves visualisation up to the user. Since each process's state is accessible after the simulation completes, a process which records its
own history can be used to visualize after the fact (or during run time by writing to a file or a shared filesystem or the network via for example a web-sockets connection).

An example of visualisation using process state can be seen in the [Boids Example](./examples/boids.md).

However, since all event history is recorded, by `Hades` itself, the framework does provide some basic visualisation functions for understanding how the processes and events interact
visually too. 

::: ki_abv.framework.hades.visualisation


