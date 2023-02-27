# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from . import Presenter, Component, Property

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
        json = {"@type":"sh:NodeShape", 
                "sh:property":[]}
        for related_prop in comp.related_properties:
                json["sh:property"].append(cls.present_property(related_prop.target))
        return json
