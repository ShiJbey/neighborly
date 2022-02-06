# Neighborly: OpenSource Town-Scale Social Simulation for Sims-Likes

Neighborly is a framework that simulates characters in a virtual town. It takes lessons learned from working with
[_Talk of the Town_](https://github.com/james-owen-ryan/talktown)
and gives people better documentation, simpler interfaces, and more opportunities for customization.

## Project Structure

```
/src/neighborly
    /ai
    /core
    /data
    /factories
    /plugins
    decorators.py
    loaders.py
    simulation.py
```

## Notes

### Task Backlog

- [ ] Remove duplicate rand num generators and create RNGManager class
- [ ] Create Factories for each of the behavior tree nodes
- [ ] Create a singular datastore for managing specifications made in YAML/XML
- [ ] EntityArchetype Authoring in YAML
- [ ] BehaviorTree Authoring in XML
- [ ] Support placing all definitions in the same file

### Non-Deterministic Behavior

The goal of having a seeded pseudo random simulation is so that users experience deterministic behavior when using the
same starting seed. We try to remove all forms of non-determinism, but some slip through. The known areas are listed
below. If you find any, please make a new issue with details of the behavior.

- N/A
