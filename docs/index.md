# Hades Overview

HADES (HADES Asynchronous Discrete-Event Simulation) is a small, user friendly framework for creating simulations in python!


* 🎲🤖 **Supports both Agent Based and Process Based models** - how you model the entities in your simulation is up to you!
* ⚡ **Async execution within a time-step** - makes working with distributed systems easy and makes improving simulation performance simple.
* 🏷️ **Pydantic style events** - gives type hints and enforcement, making it easy to see what an event will contain and improving developer experience
* 📦 **Encapsulated simulated processes** processes or agents are encapsulated, keeping state manageable and processes easy to swap in or out

## Getting Started 

```bash
pip install hades-framework
```

```python
from hades import Hades, Process, Event
```



## Contents

[Design Justification](./design-justification.md) - Hades is a general purpose framework designed with a particular focus on the needs of simulation and validation of algorithmic underwriting strategies at Ki Insurance.
[Core Framework](./core.md)
[Time Module](./time.md) - A package of utilities for dealing with times and dates within a simulation
[Visualisation](./visualisation.md) - Notes on using Hades for visualisation
