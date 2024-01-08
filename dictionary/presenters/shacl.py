# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from . import Presenter, Type, Component, Property

class SHACLPresenter(Presenter):
    Mimetype="application/shacl+json"
    @classmethod
    def present_property(cls, prop : Property):
        json = {"@type":"sh:PropertyShape"}
        json["sh:path"] = prop.uri
        json["sh:description"] = prop.description
        json["sh:name"] = prop.title
        json["sh:minCount"] = prop.lower
        if prop.upper > 0:
            json["sh:maxCount"] = prop.upper
        return json

    @classmethod
    def present_component(cls, comp : Component):
        json = {"@type":"sh:NodeShape", 
                "sh:property":[]}
        for related_prop in comp.related_properties:
                json["sh:property"].append(cls.present_property(related_prop.target))
        return json

    @classmethod
    def present_type(cls, type : Type):
        #FIXME - just flattening properties for demonstration for now.
        json = {"@type":"sh:NodeShape", 
                "sh:property":[]}
        for related_comp in type.related_components:
                shape = cls.present_component(related_comp.target)
                for prop in shape["sh:property"]:
                    json["sh:property"].append(prop)
        return json