# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from . import Presenter, Model, Component, Property
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
        for assignment in comp.property_assignments:
            ctx.append({assignment.key:cls.present_property(assignment.property)})
        return ctx

    @classmethod
    def present_type(cls, type : Type):
        ctx = []
        for assignment in type.component_assignments:
            ctx.append({assignment.key:"@nest"})
            for item in cls.present_component(assignment.component):
                ctx.append(item)
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

    @classmethod
    def present_type(cls, type : Type):
        return {"@context":JSONLDContextPresenter.present(type), 
            **jsonschema_default.create_from(JSONSchemaPresenter.present(type))}
