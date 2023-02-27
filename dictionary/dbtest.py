# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from sqlalchemy import insert, values, select
from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker
from database import Base

from models import Item, Property, Component, ComponentPropertyRelation, State

from sqlalchemy import select

engine = create_engine('sqlite:///:memory:')

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

session = SessionLocal()

"""

c1 = Component(uri="http://ifc.org/Wall", title="c1")
c2 = Component(uri="http://ifc.org/Slab", title="c2")

p1 = Property(uri="http://schema.org/length", title="p1")
p2 = Property(uri="http://schema.org/material", title="p2")

session.add_all([c1, c2, p1, p2])
session.commit()


ComponentPropertyRelation(source=c1, target=p1).post(session)
ComponentPropertyRelation(source=c1, target=p1).post(session)
ComponentPropertyRelation(source=c1, target=p2).post(session)
session.commit()

s1 = State()

s1.post(session)
session.commit()


assert ComponentPropertyRelation.get(session, c1.id, p1.id).refs == 2

c11 = Component(uri="http://ifc.org/Wall", title="c11")
c11.post(session)

s2 = State()

s2.post(session)
session.commit()

"""

slab = Component(uri="http://ifc.org/Slab")
wall = Component(uri="http://ifc.org/Wall")
length = Property(uri="http://schema.org/length")
material = Property(uri="http://schema.org/material")
    
items = [slab, wall, length, material]
   
for item in items:
        item.post(session)
    
ComponentPropertyRelation(source = slab, target= length).post(session)
ComponentPropertyRelation(source = slab, target= material).post(session)
ComponentPropertyRelation(source = wall, target= material).post(session)
session.commit()
#ComponentPropertyRelation(source=c1, target=p1).delete(session)
#assert ComponentPropertyRelation.get(session, c1.id, p1.id).refs == 1
#ComponentPropertyRelation(source=c1, target=p1).delete(session)
#assert not ComponentPropertyRelation.get(session, c1.id, p1.id)
#session.commit()


