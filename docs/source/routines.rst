Routines
========

**Routines are a hold-over feature from an older version of Neighborly. Their API is going to be
refactored to better align with the new AI architecture. This is a description of the current
implementation. The new implementation will allow characters to schedule Goals rather than
locations.**

Weeks in Neighborly is represented as seven 24-hour days. We needed a way for character to know
where they needed to be at a given time. So, Routines provide an API for saying what location a
character should be at any given time. Each routine maintains a dictionary of daily routines
with collections of routine entries for that day.
