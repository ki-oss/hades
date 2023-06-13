
Here we are going to build a simple simulation where we simulate Zeus sending lightning bolts and Poseidon creating storms, both potentially affecting the life of Odysseus

#### Imports

```python
--8<-- "examples/readme_usage.py:0:4"
```

#### Defining our Events

Let's begin by defining some events we want to exist. Lets have one for Zeus throwing lightning at a target, one for Poseidon causing a storm near a target, one for Athena Intervening to help someone, and one for Odysseus dying.

```python
--8<-- "examples/readme_usage.py:15:28"
```

#### Adding the God Processes

Okay now we have our events we need some processes to actually do stuff with them. Let's start by defining some simple ones for Zeus and Poseidon to simply use their powers on Odysseus at intervals. To do this they can
react to the builtin `SimulationStarted` event.


```python
--8<-- "examples/readme_usage.py:34:51"
```


#### Adding Odysseus' Process


Now lets do this for our hero Odysseus. We want to make it so that Odysseus will take a random amount of damage when he is the target of a `LightningBoltThrown` or `StormCreated`, if his health points are depleted we will set his state
to deceased using an Enum.

```python
--8<-- "examples/readme_usage.py:9:12"
```

Finally if `AthenaIntervened` his health will be restored and he will be `SAFE`.

```python
--8<-- "examples/readme_usage.py:68:107"
```

#### Adding Athena's Process

Last lets add the crucial Athena process. Let's have her do two things. Firstly, similar to `Poseidon` and `Zeus` lets make her have some predefined time to act. At `t=3` say where she will, no matter what, intervene.

Secondly, whenever `OddyseusDied` she will have a `50%` chance of intervening. Note that this will happen on the same timestep! See [API Reference > Hades](../api_reference/hades.md) for more on how this works!


```python
--8<-- "examples/readme_usage.py:54:66"
```

#### Putting it all together

Finally we want to actually run these processes together

```python
--8<-- "examples/readme_usage.py:113:120"
```

Note how we instantiate `Odysseus` and `Athena` with a random seed to ensure every time we run this we get the same result. They inherit from [`RandomProcess`](../api_reference/process.md#hades.core.process.RandomProcess) to do this.

We could also vary this over multiple runs to have an idea of how long `Odysseus' adventure lasts on average.


#### Simulation Output

Running the above we get the following output:
```
odysseus is in danger from Zeus' lightning bolt!
odysseus' health dropped to 77
odysseus is in danger from Poseidon's storm!
odysseus' health dropped to 63
but athena intervened saving and healing odysseus to 100
odysseus is in danger from Poseidon's storm!
odysseus' health dropped to 78
odysseus is in danger from Poseidon's storm!
odysseus' health dropped to 65
odysseus is in danger from Poseidon's storm!
odysseus' health dropped to 42
odysseus is in danger from Poseidon's storm!
odysseus' health dropped to 42
odysseus is in danger from Zeus' lightning bolt!
odysseus' health dropped to 30
odysseus is in danger from Poseidon's storm!
odysseus' health dropped to 0
odysseus died
athena was too late to save odysseus
```



