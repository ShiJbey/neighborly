Design Justifications
=====================

Building this simulation has been a learning experience. Its architecture has taken many
forms. And with each one, I inched closer to my ideal design. Along the way, I have
found it necessary to justify to myself why I made certain decisions over others. This
document serves as a beacon for myself when I doubt a design decision, and an
explanation to others for why things are the way they are

Why use YAML for configuration?
-------------------------------

I wanted configuration to be simple and stress free for people who are not well-versed
in computer programming. XML and JSON where my main two alternatives. However, while XML
sounds fancy and is used by many games like *The Sims*, it can feel intimidating to look
at. YAML is more readable since users don't need to worry about angle brackets. I
rejected JSON for similar reasons. YAML doesnt require the curly brackets and square
brackets to defines maps and lists. Interestingly enough, YAML is a superset of JSON,
so JSON files are still supported.

Other applications that use YAML for configuration are Docker, Ansible, and Kubernetes.

Why use an entity-component system?
-----------------------------------

When I first started working on this project, I was interested in trying an ECS
architecture because of the potential performance gains. My plan was to have many agents
operating within a single simulation, and I wanted to ensure that users would not have
to wait tens of minutes for the simulation to run. Since the whole simulation is written
in Python, I should have tempered my expectations.

After working on this project for over a year, I have come to appreciate the true
benefit of using the ECS architecture for this project. That benefit is the ability to
handle the combinatorial complexity of an extensible simulation housing heterogeneous
characters that interact with each other and the environment. Standard object-oriented
class inheritance would not have properly handled the level of customization that I
wanted users to have. Moreover, the ECS architecture makes it easier to search for
particular entities in the world.



.. toctree::
    :maxdepth: 2
    :caption: Contents:

    index.rst
    installation.rst
    working_with_ecs.rst
    relationships.rst
    event_driven_architecture.rst
    design_justifications.rst

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
