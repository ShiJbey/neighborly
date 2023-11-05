.. _settlements:

Settlements and Districts
=========================

Settlements are the starting point for the procedural generation process. They set the stage for the types of themes that might emerge from characters interactions, and are the first place that users have the ability to express their authorial intent for what the shape of the settlement will be.

**Settlement Fields**:

- ``settlement_name``: String text name for the city. Users can also use Tracery rules to define the settlement name
- ``districts``: The IDs of district definitions that make up the settlement

Settlements are divided into one or more districts. Each district defines what types of businesses exist within it and the character types that exist within it. So continuing our Night city example, we define districts within their own JSON file. Each district has a display name, text description, lists of business/residence/character types that can spawn there, and a number of residential/commercial building slots. Currently, districts cannot have subdistricts.

**District Fields**:

- ``display_name``: String text name for the city.
- ``description``: A short text description.
- ``business_types``: (1) The ID of a business definition, or (2) A mapping containing a business definition ID, and a spawn frequency override value.
- ``residence_types``: (1) The ID of a residence definition, or (2) A mapping containing a residence definition ID, and a spawn frequency override value.
- ``character_types``: (1) The ID of a character definition, or (2) A mapping containing a character definition ID, and a spawn frequency override value.
- ``business_slots``: The maximum number of businesses the district can support. (default is 0)
- ``residence_slots``: The maximum number of residential buildings the district can support. (default is 0)

Below are examples of settlement and district definitions inspired by Night City from *Cyberpunk 2077*.

.. code-block:: json

   {
      "cyberpunk_city": {
         "display_name": "Night City",
         "districts": [
               "tech_hub",
               "underground_market",
               "nightclub_district"
         ]
      }
   }

.. code-block:: json

   {
      "tech_hub": {
         "display_name": "Tech Hub District",
         "description": "The heart of technological innovation and corporate influence.",
         "business_types": [
               "tech_company",
               {
                  "definition_id": "cyber_clinic",
                  "max_instances": 2,
                  "spawn_frequency": 2
               }
         ],
         "character_types": [
               "corporate_executive",
               "hacker"
         ],
         "residence_types": [
               "high-rise_apartment",
               "luxury_condo"
         ],
         "business_slots": 5,
         "residential_slots": 3
      },
      "underground_market": {
         "display_name": "Underground Market District",
         "description": "A haven for black market deals and shady characters.",
         "business_types": [
               "black_market_vendor",
               "illegal_implant_clinic"
         ],
         "character_types": [
               "smuggler",
               "fixer",
               "cyber-enhanced_thug"
         ],
         "residence_types": [
               "cramped_apartment"
         ],
         "business_slots": 4,
         "residential_slots": 2
      },
      "nightclub_district": {
         "display_name": "Nightclub District",
         "description": "Where the city comes alive at night with music and neon lights.",
         "business_types": [
               "nightclub",
               "underground_rave"
         ],
         "character_types": [
               "partygoer",
               "DJ"
         ],
         "residence_types": [
               "loft_apartment",
               "penthouse"
         ],
         "business_slots": 6,
         "residential_slots": 3
      }
   }
