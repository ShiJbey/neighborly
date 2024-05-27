.. _location-preferences:

Location Preferences
====================

.. attention:: This page needs to be updated for version 3

Neighborly does not model the exact location of characters, businesses, and residences within the simulated world. Since the simulation progresses in single-month steps, it instead calculates and records the locations that character is most likely to frequent during a given month.

The aside from places like a character's home and work place, other locations are selected to be frequented by a character based on a character's location preferences. Location preferences are rules that a character has that provide numeric scores for how much or how little a character would like to frequent that location. For example, a ``shopaholic`` trait might give a character a location preference for businesses with ``department_store`` or ``shop`` traits.

Location preferences can be added using traits and specified within the ``effects`` section of a trait definition. See the example below. Here we define the ``shopaholic`` trait and add a new location preference using the ``AddLocationPreference`` effect. This effect has two parameters, preconditions and a probability. If the location meets the preconditions, we add the probability value to it's score. The a locations final score is the average of all applied rules including a base score of 0.5. Not able exceptions are when a rule has a probability of 0.0 or < 0. A score of 0 will result in a final score of zero, regardless of the average. This helps to enforce that some characters will never be at a location. And if a rule returns a value less than zero, then the consideration is ignored and not included in the averaging calculations.

.. code-block:: json

    {
        "shopaholic": {
            "display_name": "Shopaholic",
            "effects": [
                {
                    "type": "AddLocationPreference",
                    "preconditions": [
                        {
                            "type": "HasTrait",
                            "trait": "department_store"
                        },
                    ],
                    "probability": 0.8
                }
            ]
        }
    }

Working with frequented locations in Python
-------------------------------------------

Users can access a character's list of frequented locations by accessing its ``FrequentedLocations`` component and they can access a locations collection of characters that frequent it by accessing the locations ``FrequentedBy`` component.

If users wish to add, update, or remove a frequented location, please using the helper functions provided in the ``neighborly.helpers.location`` module.

How are frequented locations updated during the simulation?
-----------------------------------------------------------

Every timestep character consider new locations to frequent. By default, characters maintain a maximum of five frequented locations. They can lose locations when a business goes permanently out of business. The built-in ``UpdateFrequentedLocationsSystem`` handles all the logistics of ensuring characters maintain a fresh set of locations.

How are frequented location used?
---------------------------------

Neighborly uses frequented locations to sample what other characters are available to form relationships when characters meet new people outside of work or home. Ever timestep there is a probability that a character will start a new relationship with someone else who shares a common frequented location. This is all implemented within the built-in ``MeetNewPeopleSystem``.

Why not have characters move based on routines?
-----------------------------------------------

Moving characters between discrete locations slowed the runtime of the simulation as every character had to consult a schedule for where they needed to be. So, for performance reasons, this was cut from the simulation.
