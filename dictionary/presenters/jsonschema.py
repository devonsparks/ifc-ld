# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from . import Presenter, Component, Property, StringProperty, ValueRangeProperty

class JSONSchemaPresenter(Presenter):
    Mimetype = "application/schema+json"
    Schema = "https://json-schema.org/draft/2019-09/schema"


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
            json["properties"][related_prop.target.title or related_prop.target.uri] = cls.present_property(related_prop.target)

        return json

    @classmethod
    def present_property(cls, prop : Property):
        json = {"title":prop.title,
                "description":prop.description
                }

        if isinstance(prop, StringProperty):
            json["type"] = "string"
        elif isinstance(prop, ValueRangeProperty):
            json["type"] = "number"
            json["minimum"] = prop.minimum
            json["maximum"] = prop.maximum
        else:
            json["type"] = "string"
        return json