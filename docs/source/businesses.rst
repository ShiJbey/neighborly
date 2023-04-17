Businesses
==========

Business are special locations within a settlement that are owned by characters and employ other
characters. They can be a useful tool for building character relationships and creating a rich
narrative setting for a story world.

Modeling Businesses
--------------------

The following is a list of components currently used to drive businesses

- `Name`: Defines the name of the business using Tracery a grammar
- `Lifespan`: Defines how long a business lives on average
- `StatusManager`: Tracks all instances of StatusComponents attached to the business
- `EventHistory`: Tracks all the life events this business has been a part of
- `Business`: Defines business-specific information
- `Location`: Marks the business as a place that characters can travel to
- `Activities`: What kinds things characters can do at a location (shopping, eating, painting, ...)
- `FrequentedBy`: Tracks characters that frequent this location
- `Building`: Describes the building the business is within
- `Services`: What services does this business offer (construction, education, law, ...)


Defining a business prefab
---------------------------

Businesses are authored using entity prefabs in YAML files. Do not forget to add the `Business`
entry under the *components* section of the prefab.

Below is an example of a business prefab in YAML. We start by defining the name of the
prefab, if it is a template, and if it extends any other prefabs. Finally, we define the parameters
for components that are attached to the business GameObject when it is instantiated.

Each component in this prefab should be registered with the ECS before instantiation. Components
without parameters need to be followed by empty curly braces ``{ }``.

When creating new business prefabs users can extend the ``business::default`` prefab to
automatically include all required components. These components can be overwritten in the new
prefab definition.

.. code-block:: yaml

    name: sample_business
    is_template: true
    extends: [
      "business::default"
    ]
    components:
        Name:
            value: "Business"
        Business: { }
        StatusManager: { }
        Location: { }
        Activities: { }
        FrequentedBy: { }
        EventHistory: { }
        Building:
            building_type: commercial
        Lifespan:
            value: 10


Loading the prefab
------------------

You can add your prefab to the simulation using loader functions included with
Neighborly.

1. ``load_business_prefab(sim.world, "path/to/yaml/file")``
2. ``load_data_file(sim.world, "path/to/yaml/file")``

There is a slight difference between these two functions. The first is intended to load
a single business prefab from a file. That is what we would use for the example
definition above. However, if we placed multiple business prefabs in the same file,
the second function would load them all at once. The only change we would need to make
the second option work is to place our definitions within a YAML list (see below).
You can always reference the included plugin code to get a better understanding of how
to use these functions.

.. code-block:: yaml

    Businesses:
        - name: "SampleBusiness"
          # Other data fields ...
        - name: "SampleBusinessVariation"
          # ...
        - name: "WacArnold's Restaurant"
          # ...


Services
--------

Services are things that the business offers customers. They may be used to cast
businesses into roles within events that require a particular business. For example,
a `ChildBirthEvent` may choose a to record a hospital where the child was born. To do
this we could search for all game objects with a ``Services`` component then filter for
``Services`` containing the *"hospital"* service. You can easily do this using the
``find_places_with_services(world, *services)`` utility function.

.. code-block:: python

    hospitals = find_places_with_services(world, "hospital")
    print(hospitals)

At this point you may be wondering how you add services to a business. This is done
within the entity prefab file. Add a "Services" entry under the *components* map and
enter the list of services. These are case-insensitive, but typos and misspellings are
not caught by the system. So, be sure to be consistent in your naming conventions.
Please note that the "Service" entry (capital *S*) has a keyword argument "service"
(lowercase *s*).

.. code-block:: yaml

    name: "business::hospital"
    extends: "business::default"
    config:
        owner_type: Doctor
    components:
        Business:
            name: "Hospital"
            employees:
                Doctor: 2
                Nurse: 3
                Secretary: 1
        # Services go here!!
        Services:
            services:
                - hospital
                - emergency_medical


Activities
----------

Much like services, users can specify what activities there are to do at a business by providing an
`Activities` component. This component is used by characters to determine what locations in a
settlement that they are most likely to frequent. Also activities may be used to filter Businesses.

Add an "Activities" entry under the *components* section of the entity prefab, and
enter the list of activity names. These are case-insensitive, but typos and misspellings are
not caught by the system. So, be sure to be consistent in your naming conventions.
Please note that the "Activities" entry (capital *A*) has a keyword argument "activities"
(lowercase *a*).

.. code-block:: yaml

    name: "Chuck-E-Cheese"
    extends: "business::default"
    config:
        owner_type: Owner
    components:
        Business:
            name: "Hospital"
            employees:
                Manager: 1
                Employee: 2
                Mascot: 1
        # Services go here!!
        Activities:
            activities:
                - eating
                - games


Character Occupations
---------------------

Occupations track what a character's job title is, where they work, and the date that they started
their job. Characters become eligible to work when they become YoungAdults. At that time,
they gain the `InTheWorkforce` status, and they `Unemployed` status if they do not already
have an occupation. Unemployed characters will all the `FindEmployment` goal to their goal set
each timestep they are missing an occupation.

Occupation Types
^^^^^^^^^^^^^^^^

An `OccupationType` is a set of information defining an occupation that a character can have.
Below is an example of an occupation type definition for a graduate student. OccupationTypes have
a name, level (representing the socioeconomic status/prestige of the position), and a collection
of rules that define when a character is eligible to hold the occupation.

Occupation rules are stored as a list of precondition tuples. All preconditions functions in a tuple
must evaluate to true for the character to be eligible to hold the occupation. If there are more
than one tuple in the OccupationType's rule variable, then only one tuple need to pass. Essentially
you can think of tuples as performing a logical-AND operation on all internal preconditions, and
the outer list performing a logical-OR across all tuples in the list.

.. code-block:: python

  # Graduate students are low on the income ladder and has a single rule that
  # requires they be a college graduate and at least a young-adult
  graduate_student = OccupationType(
    name="Graduate Student",
    level=1,
    rules=[
      (
        lambda gameobject: gameobject.has_component(CollegeGraduate),
        lambda gameobject: gameobject.get_component(LifeStage).life_stage
          >= LifeStageType.young_adult
      )
    ]
  )

Occupation type definitions are stored in the ``OccupationTypes`` static class for look-up at
runtime. Note that the class name is plural to differentiate it from the class that contains a
single definition.

.. code-block:: python

  # This registers the occupation type for construction
  OccupationTypes.add(graduate_student)

Occupation types are used within YAML entity prefab definitions under the ``owner_type``
or ``employee_types`` fields for for Business components.

.. code-block:: yaml

  name: University Laboratory
  components:
    Business:
      owner_type: Professor
      employee_types:
        Graduate Student: 5 # <== Here we use the name of the occupation type
    # ... other component information


At runtime, Neighborly uses this information to instantiate new `Occupation` components.

**Authoring Note**: Simulation authors need to define all the occupations that could appear in their
simulation. Plugins that feature new businesses should be especially sure to load the new occupation
type definitions when creating new business prefabs.

Tracking characters' work history
---------------------------------

There may be times when we want to characters to only be eligible for a position if they have prior
experience with particular occupations. This is the `WorkHistory` component's job. Every time a
character stops an occupation, a new entry is added to the WorkHistory component. It tracks the
the occupation title, the business they worked at, the number of years they held the job, and their
reason for leaving (if any).

Neighborly provides utility functions for WorkHistory queries. They can be imported from
``neighborly.utils.query``.

1. ``has_work_experience_as(occupation_type: str, years_experience: int = 0)``: Returns a
precondition function that returns true if a character has at least the given given years of
experience as a given occupation_type.
2. ``get_work_experience_as(occupation_type: str)``: Returns a function that calculates the total
amount of time (in years) that a character has held the given occupation_type across all entries.
3. ``has_any_work_experience(years_experience: int = 0)``: Returns true if the character has a total
amount of work experience exceeding the given amount.


Business-related status components
----------------------------------

- `OpenForBusiness`, `ClosedForBusiness` - As their name implies, these components tag businesses as
  being open or closed for business. Open businesses are places that characters can travel and
  work. Closed businesses have no-one working their and usually no longer exist within the
  settlement.
- `InTheWorkforce`` - Tags a character that is old enough to work
- `Unemployed` - Tags a character that is old enough to work, but does not have an occupation
- `BossOf`, `EmployeeOf`, `CoworkerOf` - These are relationship statuses that characters gain based
  on their position at the business. Relationship stats are attached to the relationship GameObjects
  and not a particular character.
- `BusinessOwner` - Tags a character as being a business owner and stores the ID of the business
  they own.


Business operating hours
------------------------

The `OperatingHours` component lets users specify when a business is open or closed to the public.
This is different than the `OpenForBusiness` and `ClosedForBusiness` statuses. This component
is used to track when characters can travel to the businesses location during any given day.

Currently, this is not utilized by any systems as it is a hold-over feature from an older version
of Neighborly.

Operating hours are stored as a dictionary where the keys are weekdays and the values are tuples
of two integers representing the span of hours that teh business is open.

Operating Hours can be specified using a few different string formats

- (interval 24HR) ## - ##
  Opening hour - closing hour
  Assumes that the business is open all days of the week
- (interval 12HR AM/PM) ## AM - ## PM
  Twelve-hour time interval
- (interval-alias) "morning", "day", "night", or ...
  Single string that maps to a preset time interval
  Assumes that the business is open all days of the week
- (days + interval) MTWRFSU: ## - ##
  Specify the time interval and the specific days of the
  week that the business is open
- (days + interval-alias) MTWRFSU: "morning", or ...
  Specify the days of the week and a time interval for
  when the business will be open

So, in your YAML prefab file, users could do the following:

.. code-block:: yaml

  name: sample_business_a
  components:
    OperatingHours:
      hours: "8AM - 4PM" # Business is open every day from 8 to 4


or something like this

.. code-block:: yaml

  name: sample_business_b
  components:
    OperatingHours:
      hours: "MWF: night" # business is open night on Monday, Wednesday, and Friday


Business-related systems
------------------------

Unemployment System
^^^^^^^^^^^^^^^^^^^

The unemployment system (currently named ``UnemployedStatusSystem``) is responsible for ensuring
that unemployed characters attempt to find employment either by finding a job or starting a new
business. Characters are given a configured amount of time to find a job before they will depart
the settlement and leave the simulation altogether with their nuclear family (spouses and dependent
children).

By default, characters are given five (5) years to find a job before they depart from the
simulation. This value can be changed by setting the ``years_to_find_a_job`` class attribute on the
``UnemployedStatusSystem`` class.

.. code-block:: python

  # Add the following line of before starting the simulation to change time to find a job
  # This example would give characters 3.5 years to find a job before they are removed
  UnemployedStatusSystem.years_to_find_a_job = 3.5


Work History
------------

Sometimes as a precondition for certain occupations we want to check if a character has a certain
amount or type of work experience. The `WorkHistory` component attached to characters stores
records of all a character's previous occupations. It gets updated when characters leave jobs and
stores information that includes the name of the occupation, where they worked, how long they
held their position, and a reason for leaving the position. Users can think of the `WorkHistory`
component as a character's resume.
