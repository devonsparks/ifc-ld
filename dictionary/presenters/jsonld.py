# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from . import Presenter, Type, Component, Property
from .jsonschema import JSONSchemaPresenter
import jsonschema_default


class JSONLDContextPresenter(Presenter):
    Mimetype = "application/ld+json"

    @classmethod
    def present_property(cls, prop: Property):
        ctx = {"@id": prop.uri}
        if prop.datatype == "http://www.w3.org/2001/XMLSchema#anyURI":
            ctx["@type"] = "@id"
        elif prop.datatype:
            ctx["@type"] = prop.datatype
        return ctx

    @classmethod
    def present_component(cls, comp: Component):
        ctx = {}
        for related_prop in comp.related_properties:
            if related_prop.target.title:
                ctx[related_prop.target.title] = cls.present_property(
                    related_prop.target)
        return ctx

    @classmethod
    def present_type(cls, type: Type):
        ctx = {
            "@context": {
                "components": {
                    "@id": "http://ifc-ld.org/specification#hasComponent",
                    "@container": "@type",
                    "@context":{}
                }
            }
        }
        for related_comp in type.related_components:
            if related_comp.target.title:
                ctx["@context"]["components"]["@context"][related_comp.target.title] = {
                    "@id":related_comp.target.uri, 
                    "@context": cls.present_component(related_comp.target)}
        return ctx


class JSONLDPresenter(Presenter):
    Mimetype = "application/ld+json"

    @classmethod
    def present_property(cls, prop: Property):
        return {"@context": JSONLDContextPresenter.present(prop),
                **jsonschema_default.create_from(JSONSchemaPresenter.present(prop))}

    @classmethod
    def present_component(cls, comp: Component):
        return {"@context": JSONLDContextPresenter.present(comp),
                **jsonschema_default.create_from(JSONSchemaPresenter.present(comp))}

    @classmethod
    def present_type(cls, type: Type):
        return {"@context": JSONLDContextPresenter.present(type),
                **jsonschema_default.create_from(JSONSchemaPresenter.present(type))}
