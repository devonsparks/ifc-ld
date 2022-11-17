# SPDX-License-Identifier: LGPL-3.0-or-later
# -*- coding: utf-8 -*-
from runtime import MemRepository, EC

"""
1.0 - Prelude
---------------------------------------------

This file is an executable tutorial of the prototype runtime system described in README.md.

"""

"""
1.1 - Repositories
---------------------------------------------

We start by creating a Repository, R, to hold data "ECs" ("Entity-Components").
Repositories can hold any number of ECs for any purpose. 
"""
R = MemRepository(EC)


"""
1.2 - ECs and EC Inheritance
---------------------------------------------

An EC is a collection of bindings (key-value pairs, similar to a JSON object literal)
and associated behavior. ECs expand on standard key-value pairs by supporting inheritance. 
An EC may have at most one "parent" EC (accessible via EC.parent()). Should a key 
(fetched via EC.get(key)) not be found in the EC, the search is repeated in the parent EC,
and so on through the parent chain, until the key is found. An error is raised in the event 
the key is not found in any EC in the parent chain.

This tree-like structure allows efficient data sharing between ECs. If a parent EC defines
a key-value pair, like {"color":"red"}, all "forked" ECs will inherit the same key-value
automatically. Forked ECs may then override the parent's value by redeclaring it within 
their bindings. 

Example:


                       EC1
                       ┌─────┬─────┐
                       │color│red  │
                       └─────▲─────┘
                             │
                             │
                             │
        EC2                  │         EC3
        ┌─────┬─────┬────────┴────────┬──────┬──────┐
        │size │large│                 │color │green │
        └─────┴─────┘                 └──────┴──────┘




EC1 defines {"color":"red"}. EC2 and EC3 are forks of EC1, each with their own id. 
EC2.get("color") returns "red" because the key "color" is found in its parent.
EC3.get("color") returns "green", because the key is found in its key-value set.

EC.get(key) has the useful property that returned values that represent other ECs are 
automatically dereferenced if they're found in the active Repository. 
"""

"""
1.3 - Declaring and setting EC key-values
---------------------------------------------

EC keys _should_ be "declared" (with EC.declare(key, [optional args])) before they 
are used. A key declaration defines meaning of a key by declaring its name (e.g., "age"),
URI ("http://dbpedia.org/ontology/age"), and its value's type (e.g., a datatype URI like "xsd:string"). 
An existing key declaration can be retrieved with EC.declaration_of(key).

Once declared, keys can be set using EC.let(key, value).
"""

ec1 = EC(R).declare("color", "https://schema.org/color", "xsd:string").let("color", "red")
ec2 = ec1.fork().declare("size").let("size", "large")
ec3 = ec1.fork().let("color", "green")

assert ec1.get("color") == "red"
assert ec2.get("color") == "red"
assert ec3.get("color") == "green"

"""
1.4 - Entities and Components
---------------------------------------------

ECs are distinguished by the set of keys they hold.

Any EC with an "id" key is an Entity. An Entity represents any asset or piece of information
you want to track over time, requiring a unique identifier. 

Any Entity with an "describes" key is a Component. Components _describe_ Entities by linking back 
to them and holding their own key-values. A Component may describe more than one Entity. 

"""

Entity = EC(R, R.get(R.put({"id":"Entity"})))
Component = Entity.fork({"id":"Component"}).declare("describes")

"""
1.5 - Linking a Component to an Entity
---------------------------------------------

Linking a Component to an Entity only requires EC.let()-ing the "describes" key.

Note that links between Components and Entities are one-way, from the Component
to the Entity. 
"""
loc_c = Component.fork().declare("lat").declare("lon")
loc_c.let("lat", -10.4).let("lon", -64)
loc_c.let("describes", Entity.fork({"id":"e1"}))

assert loc_c.get("describes").get("id") == "e1"

"""
1.6 - Creating new kinds of relations on ECs
---------------------------------------------

EC keys can have values that are other ECs, allowing users to model networks or graphs of ECs.
This can be especially useful for modeling relationships. 

To set up a relation key, first declare it using EC.declare(key, uri). Then use let(key, value), 
where value is another EC. Calling let(key, EC) on the same key multiple times will create a 
list of linked ECs on the key. 


                                    a_wall
        wall_building_decomp           ▲
        ┌─────────────┬────┐           │
        │describes    │    ├───────────┘
        ├─────────────┼────┤
        │decomposes   │    ├───────────┐
        └─────────────┴────┘           │
                                       ▼
                                   a_building

"""
RelDecomposes = Component.fork().declare("isdecomposedby", "ifc5:isdecomposedby").declare("decomposes", "ifc5:decomposes")


a_building = Entity.fork({"id":"a_building"})
a_wall = Entity.fork({"id":"a_wall"})
building_wall_decomp = RelDecomposes.fork().let("describes", a_wall).let("decomposes", a_building)

assert building_wall_decomp.get("describes").get("id") == a_wall.get("id")
assert building_wall_decomp.get("decomposes").get("id") == a_building.get("id")

"""
1.7 - Snapshotting ECs
---------------------------------------------

Because ECs can be linked, and their key-values depend on those they inherit from, it can be difficult
to see the complete state of an EC with the operations described so far. EC.snapshot() solves this, by 
returning a snapshot of the complete state of the EC, including all inherited key-values, and resolving
all linked ECs.

>>> print(json.dumps(ec3.snapshot()), indent=4)
{
	"@context": {
		"id": "44f292f6-156d-4086-9c58-e0651c8056c7",
		"color": {
			"@id": "https://schema.org/color",
			"@type": "xsd:string",
			"id": "3fa63abf-710a-4377-87d9-ed9b2611e939"
		}
	},
	"color": "green",
	"*": {
		"id": "06162471-4e4e-493c-b4d0-a456ab154bbe",
		"@context": {
			"id": "44f292f6-156d-4086-9c58-e0651c8056c7",
			"color": {
				"@id": "https://schema.org/color",
				"@type": "xsd:string",
				"id": "3fa63abf-710a-4377-87d9-ed9b2611e939"
			}
		},
		"color": "red"
	},
	"id": "f5cebca3-3337-4637-8a7f-c6bb63b7abe6"
}

"""

"""
1.8 - Transferring ECs to another Repository
---------------------------------------------
Because EC.snapshot() returns a point-in-time snapshot of an EC's state, it can be used to 
transfer an EC network to another Repository. EC.transfer(repository) solves
for this. 
"""

R2 = MemRepository(EC)

assert not R2.get("a_building")
a_building.transfer(R2)
assert R2.get("a_building").get("id") == "a_building"

"""
1.9 - Conclusion; where to go from here
---------------------------------------------
The EC model prototyped here provides a compact API for modeling and browsing networks
of linked information. It is just a starting point. The real work is in testing its
limits by trying to model Entities and Components useful in practice. Patterns around 
the use of multiple Repositories and EC.transfer() could also use more attention. 

Challenges to the model proposed here are welcome. However, the features of this EC
model were carefully chosen, and many of them are codependent. Alternative positions
are best demonstrated with working code - either by modifying the existing prototype,
or sharing another.
"""

