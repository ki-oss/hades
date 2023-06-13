## Overview

Let's try to use LLMs to simulate the story of the Odyssey being retold, but with a slight difference:
> Odysseus has a knowledge of and can use modern technology

Using LLM API's and calling them asynchronously is a useful demonstration of the type of [IO-Bound](../guides/performance.md#io-bound) workloads which Hades is designed around.
This will also illustrate some interesting features of the event loop.

## Designing the processes

The processes and how they interact is the key to this simulation. The key idea is that we have a bit of a loop, which is enabled by the [hades event loop](../api_reference/hades.md#event-loop):

```mermaid
flowchart TB
    A[Homer records these and plans to synthesise them into a coherent story tomorrow]
    C[Homer notifies the characters of the last day's story]
    D[Odysseus]
    E[Athena]
    F[Zeus]
    G[...]
    H[OpenAI endpoint]

    subgraph Characters act according to their character the last day's story
        D
        E
        F
        G
    end

    subgraph Homer
        A
        C
    end

    A -->|time moves forward one day| C

    C -.->|async| D
    C -.->|async| E
    C -.->|async| F
    C -.->|async| G
    D -->|CharacterActed| A
    E -->|CharacterActed| A
    F -->|CharacterActed| A
    G -->|CharacterActed| A
    D -.->|async| H
    E -.->|async| H
    F -.->|async| H
    G -.->|async| H
```

## Implementation

### Processes

The core logic is within the processes 

```python
--8<-- "examples/multi_agent_llm_storytelling/processes.py"
```
### Additional Code

??? "Event Definitions"
    ```python
    --8<-- "examples/multi_agent_llm_storytelling/events.py"
    ```

??? "LLM Prompts"
    ```
        --8<-- "examples/multi_agent_llm_storytelling/prompts.py"
    ```
??? "Utilities"
    ```python
    --8<-- "examples/multi_agent_llm_storytelling/utilities.py"
    ```

### Putting it all together

```python
--8<-- "examples/multi_agent_llm_storytelling/simulation.py"
```


## The resulting story


--8<-- "examples/multi_agent_llm_storytelling/output.txt"

