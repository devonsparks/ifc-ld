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
    def present_state(cls, state : State):
        pass
    
    @abc.abstractclassmethod
    def present_index(cls, object : dict):
        pass

    @classmethod
    def all(cls):
        for subclass in cls.__subclasses__():
            yield from cls.all(subclass)
            yield subclass


#from .jsonld import JSONLDPresenter
#from .jsonschema import JSONSchemaPresenter
from .html import HTMLPresenter
#from .shacl import SHACLPresenter
from fastapi.responses import HTMLResponse
def present(object, accept):
    """
    for presenter in Presenter.all():
        if presenter.Mimetype == mimetype:
            return presenter.present(object)
    return object
    """
    #FIXME Order is arbitrary; should go in order of accept
    mimes = accept.split(",")
    #if JSONLDPresenter.Mimetype in mimes:
    #    return JSONLDPresenter.present(object)
    #elif JSONSchemaPresenter.Mimetype in mimes:
    #    return JSONSchemaPresenter.present(object)
    #elif SHACLPresenter.Mimetype in mimes:
     #   return SHACLPresenter.present(object)
    if HTMLPresenter.Mimetype in mimes:
        return HTMLResponse(content=HTMLPresenter.present(object))
    else:
        return object
