# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from . import Presenter, Type, Component, Property
from jinja2 import Environment, FileSystemLoader, select_autoescape


class HTMLPresenter(Presenter):
    Mimetype="text/html"
    Env = Environment(
        loader=FileSystemLoader('static'),
        autoescape=select_autoescape())

    @classmethod
    def present_property(cls, prop : Property):
        types = set()
        comps = set()
        for assignment in prop.component_assignments:
            for superassigment in assignment.component.type_assignments:
                types.add(superassigment.type)
                comps.add(assignment.component)
        return cls.Env.get_template("resource.template.html").render(resource = prop.__dict__, types=types, comps=comps)

    @classmethod
    def present_component(cls, comp : Component):
        return cls.Env.get_template("resource.template.html").render(resource = comp.__dict__)

    @classmethod
    def present_type(cls, type : Type):
        types = set([type])
        comps = set()
        props = set()
        for assignment in type.component_assignments:
            for subassigment in assignment.component.property_assignments:
                comps.add(assignment.component)
                props.add(subassigment.property)
        return cls.Env.get_template("resource.template.html").render(resource = type.__dict__, comps=comps, props=props)

