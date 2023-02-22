# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from typing import List
from pydantic import BaseModel, AnyUrl
        

class Base(BaseModel):
    pass

class Item(Base):
    id: AnyUrl
    title: str = ""

    class Config:
        orm_mode = True



class Property(Item):
    datatype : AnyUrl = None
    lower : int = 1
    upper : int = -1
    ordered : bool = True

    class Config:
        orm_mode = True



class Component(Item):
    class Config:
        orm_mode = True


class State(Item):
    class Config:
        orm_mode = True
