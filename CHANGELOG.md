# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres mostly to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html). However, all releases before 1.0.0 have breaking changes
between minor-version updates.

## [3.0.0] - Unreleased


## [2.5.0] - 2024-03-24

This version introduces minor breaking changes to the content authoring pipeline. Please check your YAML and JSON files.

### Changed

- Convert content definition classes to use Pydantic

### Added

- Tag-based content selection to all authored content libraries (special thanks to @Acer-Cristea)
- Content definition compiler that allows for variants and templates
- Additional fields to all content definitions

### Removed

- Removed some fields from content definitions

## [2.4.1] - 2023-11-20

### Fixed

- List construction error when compiling all event considerations

## [2.4.0] - 2023-11-19

### Fixed

- Businesses were missing business owners

### Changed

- `GameObjectManager.has_gameobject()` now accepts an int as the parameter instead of a `GameObject` instance.

### Added

- Additional "Min/Max" column to stats table when using inspection API
- Added back support for YAML data files
- Added back `Component.on_add()` and `Component.on_remove()` lifecycle functions.
- Added social rule support for modifying incoming relationships.
- Revised the inspection API to be expandable and display custom components.
- `LifeEvent.dispatch()` now accept an optional boolean parameter to disable logging while still notifying listeners.
- Added `EventConsiderations` resource as a way to add additional considerations to pre-authored events.
- Implemented default skills for character definitions

## [2.3.1] - 2023-11-08

### Fixed

- Fixed typo that ignored events base probability score

## [2.3.0] - 2023-11-08

### Added

- Added life events for creating/dissolving friendships and enmities
- Added trait tracking for biological parents/step parents
- Added event for forming romantic crushes
- Added possibility for romantic infidelity
- Married characters move into the same house
- Adult characters will try to move into their own homes
- Add widow trait to relationships when spouses die

## [2.2.0] - 2023-11-07

### Changed

- Changed location preference rules to use probability scores and arithmetic mean calculations
- Changed life event considerations to use arithmetic mean calculations

### Added

- Added `BatchRunner` and `Metric` classes to assist with data analysis across multiple simulation runs
- Added utility functions for converting various data to Polars DataFrames

## [2.1.1] - 2023-10-30

### Fixed

- `open_to_public` field now adds `OpenToPublic` component to help locations appear as candidates
  to be frequented by characters.
- `monthly_effects` associated with job roles are now applied every timestep.
- Relationships are deactivated when a character departs or dies.
- Characters cannot gain the `lethargic` and `energetic` traits at the same time.
- Replaced `Event` type hints for `GlobalEventHistory` with `LifeEvent`.

## [2.1.0] - 2023-29-10

### Added

- New inspection functions to the `neighborly.inspection` module
- Added back non-notebook samples to facilitate library debugging

### Changed

- Moved some of the test data to become default plugins to assist new users
- Tweaked some considerations and probabilities to get more believable event histories

### Fixed

- Adjusted trait configurations to provide a better spread of relationship stats
- Fixed event considerations that cause over reproduction and unwanted polyamory
- Added `force=True` to logging config to allow logging to work in Google Colab
- Fixed `StartDating.instantiate` method that was missing a return statement

## [2.0.0] - 2023-10-27

This version breaks nearly all aspects of previous versions. Neighborly's internal architecture
was rewritten to better support data-driven authoring workflows. While version 1.0.0 started to
move away from the data-driven aspects, it made content authoring more difficult. This latest
version was built with the authoring interface holding prime importance.

### Added

- New trait system
- New skill system
- Load entire Tracery grammars straight from JSON files
- Simplified datetime representation
- Reduced ECS feature set
- Simplified simulation config

### Removed

- Support for authoring content using YAML. Now only supports JSON.
- Grid-style world map
- Server support
- Commandline interface support
- Entity prefab support
- Sphinx docs
- Goal system

## [1.0.1]

### Removed

- Removed generic parameters from `IComponentFactory` and `Stat` classes.

## [1.0.0] - 2023-08-16

Version 1.0.0 departs significantly from previous Neighborly releases. This version emphasizes simplicity, focusing
more on Neighborly's use as a data science and prototyping tool. This change reflects my evolving understanding of my
research and its place in the academic universe. To match this, most samples have been converted to encourage
experimentation and showcase data visualizations.

The passage of time has been greatly simplified to only simulate one year at a time. Since we no longer model more
granular time steps such as hours, there is no need for character routines or operating hours. We also do not need
to track the maximum capacity of a location or mark locations as eligible for travel.

Neighborly moved away from the data-driven approach of loading prefab definitions from
external files. Creating characters or businesses this way required duplicate
definitions and made it harder to share and modify existing prefabs. The new
`CharacterType` and `BusinessType` classes are a return to using factory objects to
instantiate GameObjects. The best part is that the factory is also a component that is
associate with the GameObject it instantiates. So, now users can easily query by
character or business type.

Below is a non-exhaustive list of changes.

### Added

- New Trait System so characters can spawn with additional components that affect their behavior.
- New Stats System to track stats and stat modifiers
- New Role system to manage things like occupations
- Experimental Inventory System to track items
- New `CharacterType`, `BusinessType` and `ResidenceType` factory classes for content authoring
- `@event_role` decorator that reduces boiler code when required to define new random life events.
- Added a role system to handle things like narrative-specific roles and occupations.
- `JobRequirementsLibrary` resource that manages all job requirements for occupations.
- Item system that tracks character inventory and item types.
- Additional API routes to the server
- Systems now have lifecycle methods for `on_create()`, `on_start_running()`, `on_destroy()`, `on_update()`,
  `on_stop_running()`, and `should_system_run()`.
- Added additional config parameters for logging to `NeighborlyConfig`
- Added `settlement_name` and `world_size` parameters to `NeighborlyConfig`

### Changed

- Converted `RelationshipFacet`s to use the new stat system
- `BuildingMap` resource to replace the `ISettlementMap` associated with the settlement instance.
- `Settlement` is now a resource instead of a component
- Spawn tables have been changed from components to resources
- Removed map and business/location tracking from the `Settlement` class
- Converted samples from python scripts to interactive python notebooks.
- Time moves at single year time steps
- Built-in systems now inherit from `System` instead of `ISystem`
- Death from old age is now a `DieOfOldAgeSystem` instead of a random life event
- Most events and character behavior are now triggered by specialized systems.
- Most built-in LifeEvents no longer use role lists to track associated GameObjects and data.
- Event listeners now only accept the dispatched event instance.
- An instance of the world state has been added to the attributes of `Event` instances.
- World methods have been divided among four classes `SystemManager`, `GameObjectManager`, `EventManager`,
  and `ResourceManager`.
- Revised relationship system and class interfaces for social rules, relationship stats, and relationship modifiers.
- Renamed `RelationshipFacet` to `RelationshipStat`.
- Renamed `--no-emit` CLI argument to `--no-output`.

### Removed

- The `OccupationType` class. Occupations are now defined as components that inherit from the `Occupation` class.
- Plugin configuration settings are no longer accepted in the `NeighborlyConfig`. Please use the `settings` section of
  `NeighborlyConfig` to pass configuration settings to loaded plugins.
- The `Routine` component class has been removed.
- The `OperatingHours` component class has been removed.
- Locations no longer track what GameObjects are present at the location since we do not model character movement.
- `RelationshipUpdateSystem`, `FriendshipStatSystem`, and `RomanceStatSystem`
- Removed all CLI args not including `--config, --output, --no-output`.

### Fixed

- Added missing dependencies to `pyproject.toml`

## [0.11.3]

- [Added] Added functions to `GameObject` and `AllEvents` classes to clear event listeners.

## [0.11.2] - 2023-05-21

- Fixed problem with non-determinism caused by VirtuesFactory iterating sets

## [0.11.1]

### Fixes

- The Tracery class is now seeded inside the Neighborly constructor

## [0.11.0] - 2023-05-05

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

- Type hints have been reformatted to prevent duplicate description warnings from sphinx. Class
  attribute type definitions have been moved out of `__init__` and the doc strings for attributes
  are placed below their type hints.
- Updated to newer build of Tracery (`tracery3`)

## [0.10.0] - 2023-03-27

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

## [0.9.4] - 2022-11-15

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

## [0.9.3] - 2022-08-15

_Initial Release._

[3.0.0]: https://github.com/ShiJbey/neighborly/releases/tag/v3.0.0
[2.5.0]: https://github.com/ShiJbey/neighborly/releases/tag/v2.5.0
[2.4.1]: https://github.com/ShiJbey/neighborly/releases/tag/v2.4.1
[2.1.1]: https://github.com/ShiJbey/neighborly/releases/tag/v2.1.1
[2.1.0]: https://github.com/ShiJbey/neighborly/releases/tag/v2.1.0
[2.0.0]: https://github.com/ShiJbey/neighborly/releases/tag/v2.0.0
[1.0.0]: https://github.com/ShiJbey/neighborly/releases/tag/v1.0.0
[0.11.2]: https://github.com/ShiJbey/neighborly/releases/tag/v0.11.2
[0.11.0]: https://github.com/ShiJbey/neighborly/releases/tag/v0.11.0
[0.10.0]: https://github.com/ShiJbey/neighborly/releases/tag/v0.10.0
[0.9.4]: https://github.com/ShiJbey/neighborly/releases/tag/v0.9.4
[0.9.3]: https://github.com/ShiJbey/neighborly/releases/tag/v0.9.3
