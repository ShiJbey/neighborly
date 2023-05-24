# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres mostly to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
There may be minor-version updates that contain breaking changes, but do not warrant
incrementing to a completely new version number.

## [0.11.3]

- [Added] Added functions to `GameObject` and `AllEvents` classes to clear event listeners.

## [0.11.2]

- Fixed problem with non-determinism caused by VirtuesFactory iterating sets

## [0.11.1]

### Fixes

- The Tracery class is now seeded inside the Neighborly constructor

## [0.11.0]

**This update has breaking changes from version 0.10.x**

### Changed

- The `Routine` component has been refactored to be a single collection of routine entries instead
  of a collection of DailyRoutines with individual entries.
- `RoutineEntry` instances now track what days they apply to.
- `RoutineEntries` now use `GoalNodes` to specify behavior instead of location IDs or alias names.
- `ActionableLifeEvent` has been renamed to `RandomLifeEvent`
- `CreateTown` has been renamed to `DefaultCreateSettlementSystem`

### Added

- A new `AIRoutineSystem` that queries a routine for an entry at the current time and adds the goal
  for that entry as a potential goal to pursue.
- Systems can now be toggled using the `active` class attribute. This affects all instances of a system and any child
  systems if it is a SystemGroup.
- Support for loading character and business spawn tables from CSV files for
  `DefaultCreateSettlementSystem`

### Removed

- `IBusinessType` was removed because it added unnecessary complexity to the component definitions.

### Updated

- Type hints have been reformated to prevent duplicate description warnings from sphinx. Class
  attribute type definitions have been moved out of `__init__` and the doc strings for attributes
  are placed below their type hints.
- Updated to newer build of Tracery (`tracery3`)

## [0.10.0]

**This update has breaking changes from version 0.9.x**

- The package has been restructured again to prevent circular dependencies. Classes are
  now separated into subpackages/modules by function. For example, all the component
  classes are within `neighborly.components` all the factories are within
  `neighborly.factories` and all the default systems are within `neighborly.systems`.
- The default plugins under `neighborly.plugins.defaults.xxxx` have been restructured
  to allow people to more easily include only the content they need. If you do not care
  about the specific plugins, `neighborly.plugins.defaults.all` will import all the
  default plugins into the simulation.
- Content libraries are now static class instances.
- GameObject prefabs should now be instantiated using the `GameObjectFactory` class
  rather than using the Prefab-specific libraries (CharacterLibrary, BusinessLibrary,
  and ResidenceLibrary).

### Added

- Content authoring `neighborly.decorators` for use in single file simulations.
- `py.typed` stub file to remove PyRight warning about Neighborly missing type stubs
- _SystemGroups_ were added to allow better systems ordering. The simulation update loop
  is now separated into 4 phases (initialization, early-update, update, and
  late-update).
- Utility-based behavior trees for goals
- Event callback are called directly from GameObjects instead of via systems
- Events are an integral part of the ECS

### Updated

- Content loading functions no longer need the world instance passed when loading assets

### Removed

- Prefab-specific libraries (CharacterLibrary, BusinessLibrary, and ResidenceLibrary) and replaced
  them with the `GameObjectFactory` static class that handles instantiating GameObjects from prefabs

## [0.9.5]

- The entire package has been restructures as some modules have moved
  out of the core module and into other packages
- Added `components` package to manage all the various built-in
  components
- Compresses the LifeEvent API to use a single class
  and moved support for queries or role lists to utility functions
- Removed `pandas` as a dependency for queries because it was too
  slow
- Separated out the default plugins into separate modules
- Revised the YAML loading API
- Revised the archetype authoring pipeline, introducing new config
  objects that hold metadata. This replaces the archetype functions
  that would have normally supplied this data.
- System priority constants are now defined using negative numbers
  this allows us to have a wider range of values for priorities below
  the built-in systems
- The `engine.py` module now handles more of the authored content
  such as archetypes
- Status system creates child gameobjects that may have time-released
  effects on the simulation state
- Consolidated redundant components such as `Gender` into a single
  component with an enum value

## [0.9.4]

**0.9.4 is not compatible with 0.9.3**

### Added

- `Building` class to identify when a business currently exists within the town vs.
  when it is archived within the ECS for story sifting.
- Systems to update business components when they are pending opening, open for business, and closed for business and
  awaiting demolition.
- New status components to identify Businesses at different phases in their lifecycle:
  `ClosedForBusiness`, `OpenForBusiness`, `PendingOpening`
- New PyGame UI elements for displaying information about a GameObject
- Strings may be used as world seeds
- `CHANGELOG.md` file

### Updated

- PyGame sample to use the new API
- Docstrings for `Simulation` and `SimulationBuilder` classes
- `SimulationBuilder` class
- Moved isort configuration to `pyproject.toml`

### Removed

- Jupyter notebook and pygame samples
- samples category from dependencies within `setup.cfg`
- `events`, `town`, `land grid`, and `relationships` fields from `NeighborlyJsonExporter`.
  These are duplicated when serializing the resources.
- `SimulationBuilder.add_system()` and `SimulationBuilder.add_resource()`. To add
  these, users need to encapsulate their content within a plugin
- Flake8 configuration from `setup.cfg`

### Fixed

- Bug in Business operating hours regex that did not recognize AM/PM strings
- `setup.cfg` did not properly include data files in the wheel build.
