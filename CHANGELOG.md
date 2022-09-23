# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres mostly to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
There may be minor-version updates that contain breaking changes, but do not warrant
incrementing to a completely new version number.

## [Unreleased]

## [0.9.4]
### Added
* `Building` class to identify when a business currently exists within the town vs.
when it is archived within the ECS for story sifting.
* Systems to update business components when they are pending opening, open for business, and closed for business and awaiting demolition.
* New status components to identify Businesses at different phases in their lifecycle:
`ClosedForBusiness`, `OpenForBusiness`, `PendingOpening`
* New PyGame UI elements for displaying information about a GameObject
* Strings may be used as world seeds

### Updated
* PyGame sample to use the new API
* Docstrings for `Simulation` and `SimulationBuilder` classes

### Removed

### Fixed
* Bug in Business operating hours regex that did not recognize