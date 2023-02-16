# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from . import Presenter, Type, Component, Property

class SHACLPresenter(Presenter):
    Mimetype="application/shacl+json"
    @classmethod
    def present_property(cls, prop : Property):
        json = {"@type":"sh:PropertyShape"}
        json["sh:path"] = prop.id
        json["sh:description"] = prop.description
        json["sh:name"] = prop.title
        json["sh:minCount"] = prop.lower
        if prop.upper > 0:
            json["sh:maxCount"] = prop.upper
        return json

    @classmethod
    def present_component(cls, comp : Component):
        json = []
        for assignment in comp.property_assignments:
            prop = cls.present_property(assignment.property)
            prop["sh:group"] = comp.id
            json.append(prop)
        return json

    @classmethod
    def present_type(cls, type : Type):
        json = {"@type":"sh:NodeShape", 
                "sh:property":[]}
        for assignment in type.component_assignments:
            for item in cls.present_component(assignment.component):
                json["sh:property"].append(item)
        return json
