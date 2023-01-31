# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from typing import List
from pydantic import BaseModel, AnyUrl
        

class Base(BaseModel):
    pass

class Resource(Base):
    id: AnyUrl
    title: str = ""
    description: str = ""

    class Config:
        orm_mode = True

class Association(Base):
    class Config:
        orm_mode = True

class Property(Resource):
    datatype : AnyUrl = None
    lower : int = 1
    upper : int = -1
    ordered : bool = True

    class Config:
        orm_mode = True

class PropertyComponentAssignment(Association):
    property_id : AnyUrl 
    component_id : AnyUrl
    key : str

    class Config:
        orm_mode = True

class Component(Resource):
    class Config:
        orm_mode = True

class ComponentTypeAssignment(Association):
    component_id : AnyUrl
    type_id: AnyUrl
    key : str

    class Config:
        orm_mode = True

class Type(Resource):
    class Config:
        orm_mode = True