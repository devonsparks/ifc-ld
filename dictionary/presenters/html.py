# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from . import Presenter, Component, Property, State
from jinja2 import Environment, FileSystemLoader, select_autoescape


class HTMLPresenter(Presenter):
    Mimetype="text/html"
    Env = Environment(
        loader=FileSystemLoader('static'),
        autoescape=select_autoescape())

    @classmethod
    def present_item(cls, item):
        type_map = {"Property":"properties", "Component":"components", "State":"states"}
        return cls.Env.get_template("item.template.html").render(item = item, type_map=type_map)

    @classmethod
    def present_property(cls, prop : Property):
        return cls.present_item(prop)

    @classmethod
    def present_component(cls, comp : Component):
        return cls.present_item(comp)
    @classmethod
    def present_state(cls, state : State):
        return cls.present_item(state)

    @classmethod
    def present_index(cls, index: dict):
        return cls.Env.get_template("index.template.html").render(properties = index["properties"],
                                                                  components = index["components"],
                                                                  states = index["states"])