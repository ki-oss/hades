
<p align="center">

<img src="https://raw.githubusercontent.com/ki-oss/hades/main/docs/img/hades_black.png" alt="Hades Logo">

</p>
<p align="center">
<img src="https://img.shields.io/badge/version-1.0.2-blue" alt="version">
<img src="https://img.shields.io/badge/License-Apache 2.0-blue.svg" alt="version">

</p>
<p align="center">
    <b>HADES</b> <i>(HADES Asynchronous Discrete-Event Simulation)</i> is a small, user friendly framework for creating simulations in python!
</p>

## Features

* 🎲🤖 **Supports both Agent Based and Process Based models** - how you model the entities in your simulation is up to you!
* ⚡ **Async execution within a time-step** - designed for working IO-bound workloads over the network (e.g. LLM APIs, db lookups, etc)
* 📈 **Visualisation** - `websockets` support to for building a custom frontend for your sim, `matplotlib` in a Jupyter notepad or simply outputting a `mermaid` diagram
* 🏷️ **Pydantic style immutable events** - give type hints and enforcement, making it clear what an event will contain
* 📦 **Encapsulated simulated processes** - processes or agents are encapsulated, keeping state manageable and making it possible to swap processes in and out
* 😊 **User friendly** - pattern matching on pydantic based events makes for an intuitive way to build simulations, while the separation of state helps avoid potential footguns!

## Installation
```shell
pip install hades-framework
```

## Usage
Using the Hades Framework is as simple as creating your custom `Process`es and `Event`s, registering them in the simulation, and letting Hades take care of the rest.

Here are some of the fun things you might do with it:

* [Boids and Websockets](https://ki-oss.github.io/hades/examples/boids) - The classic Boids simulation with canvas and d3.js visualisation via websockets.
    ![boids example](https://raw.githubusercontent.com/ki-oss/hades/main/docs/img/boids.gif)
* [Multi Agent LLM Storytelling](https://ki-oss.github.io/hades/examples/multi) -  Retelling the Odyssey with LLMs - demonstrates the highly IO bound stuff hades is good at. Some output:
    >   "He remembered the sea nymph who had helped him before and realized that having allies like her was crucial to his success. 
        He also continued to use his technological knowledge to stay ahead of Poseidon's wrath, utilizing his drone and sonar to navigate the waters safely."
* [Battery charging station](https://ki-oss.github.io/hades/examples/battery-charging-station) - to help compare what building a simulation looks with `simpy` vs `hades`
