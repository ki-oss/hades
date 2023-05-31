# HADES - Design Justification

## Original Goal and Problem

The goal from which HADES originates is that of creating a framework which makes it easy to simulate how an insurance company's portfolio would 
change over time given different scenarios. As these scenarios get more complex, problems begin to emerge:

1. How can we handle state in a manageable way - e.g. needing to track which policies we have written and claim incurred in a simulated book to impact future portfolio management
1. We begin coming across situations where we need to do simulation. E.g. If one thing changes in the past, we can't ignore its effect on things which come after it. 

## Requirements

Given this goal, the requirements in more depth are as follows:

1. Functional requirements:
    1. It needs to simplify handling things which change over time
    2. It needs to have a convenient way of handling state - e.g. the state of policies should only be tracked by elements which care about policies
    3. It needs to be be easy to combine sources of data - e.g. combining real with generated quotes, historic broker behaviour with simulated behaviour, historic catastrophes with hypothetical ones

2. Technical requirements - coming from the perspective of interacting with our existing software:
    1. It should be able to interact with distributed systems - e.g. calling services over the network which may or may not be running on the same physical or virtual machine
    2. It should reasonably fast (to enable its use in certain optimization approaches) - e.g. within the constraints of things having to happen in order, it should be as speedy as is relatively easily achievable
    3. It should be python based

3. User experience requirements - coming from a 'designing software for humans' point of view:
    1. It should be as easy to understand and use as possible for users with limited software development experience
    2. It should be plug-in and play: users shouldn't need to understand the entirety of a simulation to alter or replace a component of it
    3. State should be encapsulated and it should be obvious where it should be.

## Evaluation Of Candidate Solutions

Given these functional requirements, research was done on typical solutions to these kinds of problems. A full list of [resources](#further-reading) is provided at the bottom.

The main conclusions I came to from this are:

### Kinds Of Simulations

Considering various simulation approaches, a DES approach seemed to best fit the problem.

Agent-Based models,approaches also seemed pretty applicable for some aspects, however when diving deeper into their handling of time and how they actually work as a simulation they
seemed to either work similarly to DES approaches[^1], potentially making some alterations to where the `step()` occurs[^2]. 

The difference typically comes down to emphasis on 'emergent behaviour' and large numbers of instances of certain entities. On the analysis
side this tends to lead to visualisations focusing on dynamics/interactions between agents as opposed to states of particular objects.

Often DES can be used interchangeably with process based simulations, however here we use the broader meaning, leaving the model to userland.

That is to say with the a DES core, Hades can be used for either agent based or process based models[^14].

Other simulation approaches e.g. System Dynamics (too abstract to give concrete specific outputs) or Continuous (too difficult to build any reasonably complex and detailed model with) approaches seem to not be applicable. 
### Time progression should be next-event based - satisfying 2.b

This means that if there are two events scheduled e.g. $e_{1_{t_1}}$ and $e_{2_{t_3}}$ the simulation framework, 
after processing $e_1$ at $t_1$ will skip $t_2$ and immediately process $e_2$. 

From a performance perspective this makes sense. The alternative - incremental time progression involves processing at every time-step,
meaning unnecessary work. If this mode is needed events can be generated for each of the time steps anyway and thus is a special, less performant case of next-event based approaches. 

From a business perspective this makes sense too. Things in insurance typically happen with reasonable gaps between them.

### Using existing frameworks

Given the above, the best existing candidate seemed to be a python library (satisfying 2.c) called Simpy[^3]. 

This library relies on python's `yield` keyword and generator functions to represent processes. It also has a nice functional design.

However upon experimenting with it a little I found a few issues with it regarding the above requirements.

From a technical perspective, 2.a would have been a bit difficult to achieve. This is because `Environment.process`, `start_delayed` etc are 'sync' coloured and I was considering that the best way to achieve 2.a and 2.b would be to gather events occurring at the same time-step so that they are executed asynchronously, allowing distributed elements to handle the concurrent processing. However this could probably be overcome by either subclassing/extending or using a fork called μSim[^4]. 

More importantly though, having experiment with it for a while the user experience seemed like it would be suboptimal. 

Firstly, the `yield` keyword's behaviour is not always intuitive and anything which adds to cognitive load or makes the framework less accessible to newer to python users subtracts from 3.a. 

Secondly the way processes need communicate is either by having references to each other. E.g. in order for process `a` to call process `b`, we must pass a reference to `a` e.g. `a(b)`.  This means that there is an implicit hierarchy built into any design which makes achieving 3.b harder. 

Thirdly, there is no clean encapsulation of state. Classes in the documentation may include multiple processes[^5] (so they can reference one another easier), or share state by mutating some mutable object passed to multiple functional processes by reference[^6]. Violating 3.c

### Taking notes from Game Development

Games are real-time, dynamic, interactive computer simulations[^7]. They are also large pieces of software contributed to by big, distributed teams who, often by necessity, cannot be aware of the full system (satisfying 3.b). It is often scripted by Game Designers who are not necessarily experienced as engineers[^8] (satisfying 3.a). Given this, we can probably learn a lot from looking at patterns used in Game Development. 

### Event/Lifecycle functions aren't the best fit

At the most basic level game engine loops (even more generally rendering loops) are a `while` loop which will often call some event functions of registered components (hollywood style)[^9]. This approach is used by the popular Unity framework[^10]. While this makes implementing components very easy, there is essentially a lack of extensibility in terms of adding different types of events since to know when to call them. It is best for systems with a fixed set of events which can occur in a loop like unity's main loop or event more simply - Ogre's[^11].

### The Observer Pattern

Looking at other patterns used in Game Development, the classic Observer Pattern[^12] gives us some nice things. A small python implementation can be seen in [Appendix C](#appendix-c) The decoupling of subjects from observers makes state management easier, it is natural for subjects to not have a direct reference to a particular observer, stemming to some extent the temptation to share state. Subjects only have to take care of sending out events to their `Observers`, not who those observers are. The paradigm of having certain events which are passed about also makes for a somewhat extensible situation where events might be shared by different `Subjects`, and therefore satisfying requirement 3.b.

However there are also some less desirable properties. Firstly the decoupling is not complete, observers have to know about their subjects. This inhibits 3.b as components of the system become less interchangeable, and makes 3.c a bit harder to achieve, and since both observers and subjects can 'see' each other, the potential for state not being encapsulated is there.

> To me, this is the difference between “observer” systems and “event” systems. With the former, you observe the thing that did something interesting. With the latter, you observe an object that represents the interesting thing that happened. -- Game Programming Patterns [^12]

A further difficulty is that observer pattern notifications typically happen instantly. There is no intermediary scheduling the events for a later point in time. 

Additionally sometimes a modelled entity would make most intuitive sense as being both a subject and an observer. 

### Event Queues

> A queue stores a series of notifications or requests in first-in, first-out order. Sending a notification enqueues the request and returns. The request processor then processes items from the queue at a later time. Requests can be handled directly or routed to interested parties. This decouples the sender from the receiver both statically and in time. -- Game Programming Patterns [^13]

As can be seen from the above, the event queue pattern essentially fixes all of our issues with the observer pattern! Woo hoo!
We will have observer like objects being notified of events and modifying their state based on them.

However we need to make some modifications and design decisions before all our requirements are met.

## Design Decisions

Now we've settled on the pattern for the framework we need to make a few design decisions

### Use a Priority Queue

Unlike the event queue described above, First-In-First-Out is not what we want for a DES where events may be scheduled far before their occurrence or perhaps even at the same time step as it! What we
want instead is a priority queue so that the events which will happen the soonest are at the front of it.


### Static Events, not Messages or Dynamic Events

So now we have a queue, what sort of things should we put on it? Dynamic events would be some sort of function which is queued and then executed (potentially altering some state) at a future time. This approach seems really tricky to trace and loses quite a lot of the nice properties regarding how plug-and-play things are. So let's rule this out.

Static events and messages are quite similar, but messages are typically terser and more like commands intended to be used in a specific way rather than data rich events upon which receives can act as they please. Therefore static events seemed to make the most sense.

### Broadcast Events

Clearly in any reasonably complex simulation, events are going to need to be listened to by a few different processes. A single cast queue would not therefore make sense.

Similarly a work-queue doesn't make sense, multiple processes may well be interested in the same events.

Potentially processes could subscribe only to certain types of events but this would add complexity for very marginal computational gain compared to broadcast and ignore. It
could also lead to patterns where certain processes only _don't_ consume certain events because they are not subscribed to it making interoperability (will process p work in sim S) and parametrisation (which events it is subscribed to in some test) entangled. 

### Multiple Writer

All processes can write events to the queue. This is in line with the plug-and-play aim of 3.b.

### Event Grouping and Async

Since we have the 2.a and 2.b requirements, we broadcast all the events for the next time-step with events out to all the processes asynchronously. This means that we process as much as we can concurrently
(where the implementation of the event notification receiving code allows). CPU-bound tasks can be offloaded to external systems this way too.

### Events On The Same Time Step.

Small consideration, but we have the option here of only allowing future events or allowing events on the same time step too. Although the future one seems cleaner
at first glance, it does mean that a lot of patterns involving 'timeless' process communication are prevented which seems like a sacrifice not worth making.

## Caveats

Obviously there are no free lunches and the framework as it is has some shortcomings

### State Is Not Shared

While I have been describing this as a feature, it also makes certain things harder and can lead to somewhat duplicate state in some cases. There are certain ways around this
e.g. taking a leaf from Simpy's book and at process `__init__` time passing in some mutable data structure to multiple processes. However this is at-the-user's own peril and not forced or encouraged by the framework. However for immutable objects this is encouraged.

### Loops Can Occur

With processes reading and writing to the queue it is possible for feedback loops to occur ad infinitum. Sometimes this can be desirable and represent an existing feedback system, however in others, especially combined with the fact that same time step events are allowed, this could lead to undesired loops if not careful. 

Suggestion here is just to be careful and that debug level logs can help! 


### Everything is public

Since all events are broadcast, there is, by default, no private communication, and processes have to enforce this by passing events with identifiers to indicate origin where necessary.

### Its not very 'battle-tested'

As a new framework, its not particularly battle tested and there may be more caveats to be uncovered! 

## Further Reading

Some stuff not referenced in the footnotes which was interesting.

* [https://www.jasss.org/18/3/9.html](https://www.jasss.org/18/3/9.html) - paper comparing sim design approaches
* [https://a-b-street.github.io/docs/tech/trafficsim/discrete_event/index.html](https://a-b-street.github.io/docs/tech/trafficsim/discrete_event/index.html)
* [https://heather.cs.ucdavis.edu/~matloff/SimCourse/PLN/SimIntro.pdf](https://heather.cs.ucdavis.edu/~matloff/SimCourse/PLN/SimIntro.pdf)
* [https://www.brianstorti.com/the-actor-model/](https://www.brianstorti.com/the-actor-model/)
* [https://www.youtube.com/watch?v=eZfj7LEFT98](https://www.youtube.com/watch?v=eZfj7LEFT98)
* [https://www.didierboelens.com/2019/01/futures-isolates-event-loop/](https://www.didierboelens.com/2019/01/futures-isolates-event-loop/)
* [https://users.cs.northwestern.edu/~agupta/_projects/networking/QueueSimulation/mm1.html](https://users.cs.northwestern.edu/~agupta/_projects/networking/QueueSimulation/mm1.html)

## Footnotes

[^1]: [The classic MASON framework](https://github.com/eclab/mason/blob/master/mason/src/main/java/sim/engine/Schedule.java))
[^2]: [Python's MESA framework](https://github.com/projectmesa/mesa/blob/main/mesa/time.py)
[^3]: [Simpy documentation. The tutorial is pretty good and instructive](https://simpy.readthedocs.io/en/latest/)
[^4]: [μSim documentation](https://usim.readthedocs.io/en/latest/source/topics/simpy.html)
[^5]: [Simpy machine shop example](https://simpy.readthedocs.io/en/latest/examples/machine_shop.html)
[^6]: [Simpy movie renege example](https://simpy.readthedocs.io/en/latest/examples/movie_renege.html)
[^7]: [Great book on architecture of game engines](https://www.oreilly.com/library/view/game-engine-architecture/9781466560017/xhtml/ch07.xhtml)
[^8]: [This distinction between scripting vs programming / Designer vs Engineer split is explained clearly in this Quora answer](https://qr.ae/prsAAZ)
[^9]: [Inversion of Control/Hollywood Principle](https://en.wikipedia.org/wiki/Inversion_of_control)
[^10]: [Nice diagram of Unity Execution of Events ordering](https://docs.unity3d.com/Manual/ExecutionOrder.html)
[^11]: [Ogre's main render loop](https://github.com/OGRECave/ogre/blob/5a8a0c1164c7a455364656cf1e6d3ec478e6b55c/OgreMain/src/OgreRoot.cpp#L830-L859)
[^12]: [Excellent article on the Observer Pattern in game programming](https://gameprogrammingpatterns.com/observer.html)
[^13]: [Excellent article on Event Queues in game programming](https://gameprogrammingpatterns.com/event-queue.html)
[^14]: [Any Logic Whitepaper](https://www.anylogic.com/upload/books/new-big-book/2-three-methods-in-simulation-modeling.pdf)
