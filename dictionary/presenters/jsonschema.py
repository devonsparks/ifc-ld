# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from . import Presenter, Type, Component, Property, StringProperty, ValueRangeProperty

class JSONSchemaPresenter(Presenter):
    Mimetype = "application/schema+json"
    Schema = "https://json-schema.org/draft/2019-09/schema"

    @classmethod 
    def present_type(cls, type : Type):
        json = {"type":"object", 
                "title":type.title,
                "description":type.description,
                "properties":{"components":{"type":"object", "properties":{}}}, 
                "required":[]
                }
        for related_comp in type.related_components:
            key = related_comp.target.title or related_comp.target.uri
            json["properties"]["components"]["properties"][key] = cls.present_component(related_comp.target)
        return json

    @classmethod 
    def present_component(cls, comp : Component):
        json = {"type":"object", 
                "title":comp.title,
                "description":comp.description,
                "properties":{}, 
                "required":[]
                }
        json["$id"] = comp.id
        for related_prop in comp.related_properties:
            key = related_prop.target.title or related_prop.target.uri
            json["properties"][key] = cls.present_property(related_prop.target)
            if related_prop.target.lower > 0:
                json["required"].append(key)
        return json

    @classmethod
    def present_property(cls, prop : Property):
        json = {"$schema":cls.Schema,
                 "title":prop.title,
                "description":prop.description
                }

        if isinstance(prop, StringProperty):
            json["type"] = "string"
            #json["pattern"] = prop.pattern
        elif isinstance(prop, ValueRangeProperty):
            json["type"] = "number"
            json["minimum"] = prop.minimum
            json["maximum"] = prop.maximum
        else:
            type_map = {"http://www.w3.org/2001/XMLSchema#string":"string",
                        "http://www.w3.org/2001/XMLSchema#float":"number",
                        "http://www.w3.org/2001/XMLSchema#boolean":"boolean",
                        "http://www.w3.org/2001/XMLSchema#integer":"integer"}
            if prop.datatype in type_map:
                json["type"] = type_map[prop.datatype]
            else:
                json["type"] = "string"
        return json