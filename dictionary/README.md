
# A Multi-Format Data Dictionary Service

This repository contains a work-in-progress implementation of a lightweight data dictionary service. It supports the definition, storage, and retrieval of:

- **Properties** , including literals and relations of various types, including cardinality restrictions.

- **Components**, which group Properties into functional categories, along with binding attributes (e.g., is the Property required in this Component).

- **Types**, which define sets of Components that together declare the complete contract of an asset.

Relationships between Types, Components, and Properties are all many-to-many. 

The service provides a simple metamodel for these types inspired by, but much simpler than, [EMOF](https://en.wikipedia.org/wiki/Meta-Object_Facility). The HTTP interface that exposes these models through content negotiation, allowing Properties, Components, and Types to be retrieved as:

- [X] The metamodel's native format, serialized as JSON (content-type: `application/json`)
- [X] JSON Schema (content-type: `application/schema+json`)
- [X] SHACL via JSON-LD (content-type: `application/shacl+json`)
- [X] A default JSON instance (content-type: `application/ld+json`)
- [ ] ECore XML
- [ ] FNO via JSON-LD 

## Usage

The service is containerized with Docker. It expects two environment variables - `POSTGRES_USER` and `POSTGRES_PASSWORD` - to be provided at startup. Once set, `docker compose up` should configure the instance, which will be available on `localhost:8002`. 

