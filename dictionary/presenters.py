# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from typing import List
from models import Property, Component, Type, StringProperty, ValueRangeProperty
import jsonschema_default 
import abc

def present(object, mimetype):
    if mimetype == "application/schema+json":
        return JSONSchemaPresenter.present(object)
    elif mimetype == "application/ld+json":
        return JSONLDPresenter.present(object)
    elif mimetype == "application/shacl+json":
        return SHACLPresenter.present(object)
    else:
        return object


class Presenter(abc.ABC):
    @classmethod
    def present(cls, object):
        if isinstance(object, Property):
            return cls.present_property(object)
        elif isinstance(object, Component):
            return cls.present_component(object)
        elif isinstance(object, Type):
            return cls.present_type(object)
        else:
            raise Exception("Unknown type {type} to present.".format(type=type(object)))
        
    @abc.abstractclassmethod
    def present_property(cls, prop : Property):
        pass

    @abc.abstractclassmethod
    def present_component(cls, comp : Component):
        pass

    @abc.abstractclassmethod
    def present_type(cls, type : Type):
        pass



class JSONSchemaPresenter(Presenter):
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



class JSONLDContextPresenter(Presenter):
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


class SHACLPresenter(Presenter):
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