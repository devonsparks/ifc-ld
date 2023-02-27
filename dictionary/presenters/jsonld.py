# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from . import Presenter, Component, Property
from .jsonschema import JSONSchemaPresenter
import jsonschema_default

class JSONLDContextPresenter(Presenter):
    Mimetype = "application/ld+json"
    @classmethod
    def present_property(cls, prop : Property):
        ctx = {"@id":prop.id}
        if prop.datatype == "http://www.w3.org/2001/XMLSchema#anyURI":
            ctx["@type"] = "@id"
        elif prop.datatype:
            ctx["@type"] = prop.datatype
        return ctx

    @classmethod
    def present_component(cls, comp : Component):
        ctx = []
        for related_prop in comp.related_properties:
            if related_prop.target.title:
                ctx.append({related_prop.target.title:cls.present_property(related_prop.target)})
        return ctx



class JSONLDPresenter(Presenter):
    Mimetype = "application/ld+json"
    @classmethod
    def present_property(cls, prop : Property):
        return {"@context":JSONLDContextPresenter.present(prop), 
            **jsonschema_default.create_from(JSONSchemaPresenter.present(prop))}

    @classmethod
    def present_component(cls, comp : Component):
        return {"@context":JSONLDContextPresenter.present(comp), 
            **jsonschema_default.create_from(JSONSchemaPresenter.present(comp))}

