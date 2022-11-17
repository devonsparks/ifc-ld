# Prototype Runtime - Python

This directory contains a small, experimental runtime derived from the IFC-LD Pre-Release 1 draft. It differs from the IFC-LD specification in a number of ways, and the spec will be updated to match the runtime's contracts and behavior should experiments prove successful. Notable differences from the existing IFC-LD spec include:

* **Rethinking Component and Entity Structure**

    We expand the definition of "Components" to support _collections_ of key-value pairs, instead of a single "contents" attribute. This significantly reduces payload size and simplified some operations for copying data. 

    Entities and Components become flavors of a base "EC" object, where an Entity is any EC with an "id" key, and a Component is any Entity with a "describes" key, indicating the Entity or Entities it describes.

* **Differential Inheritance**

    Earlier prototypes had to do a lot of bookkeeping to allow objects to share data with each other. Introduction of a lexical "environment model" simplifies this significantly, because name resolution can be delegated to linked "parent" objects.

* **Not Packages, Repositories**

    The prototype does not support Packages as defined in the IFC-LD Pre-Release 1 specification. Instead, it introduces a "Repository" concept, which acts as a storage container for EC instances. The Repository API is intentionally closely matched to standard HTTP verbs, anticipating a standard OpenAPI specification for Repositories in a later phase.

* **Sneaking in Linked Data**

    The prototype tries to hide the mechanics of linked data integration by recasting it as variable declaration. Clients `declare()` key names and type information on ECs before use, and the system transparently updates the underlying JSON-LD "@context" object. Keys can be used on ECs without declaration, but the system will issue a warning.

* **Parlor Tricks**

    There are several new operations made possible by the above changes. Understanding their proper use, and finding new operations, is part of the fun. Of special interest are:
    - `resolve(key)`, which builds a spanning tree from a given key
    - `snapshot()`, which serializes an EC into a fully resolved spanning tree for downstream consumption
    - `transfer(repository)`, which provides a simple way to migrate ECs between Repositories.

    
[tutorial.py](tutorial.py) has a guided tour of the prototype's major capabilities. Visit [runtime.py](runtime.py) to see under the hood. 

The runtime assumes you have Python3 but has no external dependencies. 