# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from models import *
import abc

class Presenter(abc.ABC):
    Mimetype = "appication/json"
    @classmethod
    def present(cls, object):
        if isinstance(object, Property):
            return cls.present_property(object)
        elif isinstance(object, Component):
            return cls.present_component(object)
        elif isinstance(object, Type):
            return cls.present_type(object)
        elif isinstance(object, State):
            return cls.present_state(object)
        elif isinstance(object, dict):
            return cls.present_index(object)
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

    @abc.abstractclassmethod
    def present_state(cls, state : State):
        pass
    

    @classmethod
    def all(cls):
        for subclass in cls.__subclasses__():
            yield from cls.all(subclass)
            yield subclass


from .jsonld import JSONLDPresenter
from .jsonschema import JSONSchemaPresenter
from .html import HTMLPresenter
from .shacl import SHACLPresenter
from fastapi.responses import HTMLResponse, JSONResponse

def present(object, accept):
    mimes = accept.split(",")
    for mime in mimes:
        if mime == HTMLPresenter.Mimetype:
            return HTMLResponse(content=HTMLPresenter.present(object))
        elif mime == JSONSchemaPresenter.Mimetype:
            return JSONResponse(content=JSONSchemaPresenter.present(object))
        elif mime == JSONLDPresenter.Mimetype:
            return JSONResponse(content=JSONLDPresenter.present(object))
        elif mime == SHACLPresenter.Mimetype:
            return JSONResponse(content=SHACLPresenter.present(object))
    return object
