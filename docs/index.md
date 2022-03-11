# Neighborly Documentation

Neighborly is a data-driven narrative social simulation engine focused on authorial control, extensibility, and
modularity. Users can configure existing functionality using YAML files or extend the simulation's behavior by creating
their own character components.

## Factories

Neighborly is a data-driven simulation. Designers specify configuration data in YAML files, and the simulation turns the
configuration into full Python objects. We rely heavily on the factory design pattern, and maintain an internal mapping
of object types to factory instances.

## Global Singletons

Some resources need to be available to all systems and it does not make sense to have duplicate copies. So, we made
things like simulation time, output, specifications, and rng global singletons. We borrow this design approach from
Kevin Dill's Game AI Architecture (GAIA) (Dill, 2021)

### Simulation Time

There is a single SimDateTime object that maintains the current time for the entire simulation

## AI Utilities/Actions

### Moving Characters

Neighborly does not model continuous character movement. Instead, characters are teleported from one location to
another.

### Calculating Distance

Locations in neighborly are always paired with a Position component. positions are given in 2D space. This does result
in loss of information for character that are on different floors of a building, but for simplicity all locations are
given based on the position of the place or structure. By default, distance is measured using euclidean distance, but
there is also support for manhattan

## Neighborly Control Flow

## Behaviors Trees

Our goal is to get the most out of behavior trees. This includes creating new nodes to support certain types of action
selection.

Behavior trees are going to be the bread and butter technology for authoring and executing agent behaviors.

Agent behaviors are atomic and during each update loop, the tree is executed to completion. If the tree fails to
successfully, execute all actions, then the agent will have to try again on their next update.

## Social Graphs

Social graphs are a templated class that wraps a directed graph implementation. We use it for tracking relationships,
but it could also be used for tagging semantic relationships. Managing agent knowledge, tracking power/influence values,
what have you.

Social graphs are like the map data of SimCity. They are additional layers that behaviors can write to.

## Character Components

Character components are classes that hold additional information used by behavior trees
