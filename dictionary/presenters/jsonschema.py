# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from . import Presenter, Type, Component, Property, StringProperty, ValueRangeProperty

class JSONSchemaPresenter(Presenter):
    Mimetype = "application/schema+json"
    Schema = "https://json-schema.org/draft/2019-09/schema"
    @classmethod
    def present_type(cls, t : Type):
        json = {
            "$schema": cls.Schema,
            "$id":t.id,
            "title":t.title,
            "description":t.description,
            "properties":{},
            "required":[], 
        }
        for assignment in t.component_assignments:
            json["properties"][assignment.key] = cls.present_component(assignment.component)
            if assignment.required:
                json["required"].append(assignment.key)
        return json

    @classmethod 
    def present_component(cls, c : Component):
        json = {"type":"object", 
                "title":c.title,
                "description":c.description,
                "properties":{}, 
                "required":[]
                }
        json["$id"] = c.id
        for assignment in c.property_assignments:
            json["properties"][assignment.key] = cls.present_property(assignment.property)
            if assignment.required:
                json["required"].append(assignment.key)
        return json

    @classmethod
    def present_property(cls, p : Property):
        json = {"title":p.title,
                "description":p.description
                }

        if isinstance(p, StringProperty):
            json["type"] = "string"
        elif isinstance(p, ValueRangeProperty):
            json["type"] = "number"
            json["minimum"] = p.minimum
            json["maximum"] = p.maximum
        else:
            json["type"] = "string"
        return json