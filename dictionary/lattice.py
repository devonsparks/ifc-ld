from sqlalchemy import Table, Column, ForeignKey, Integer, String, CheckConstraint, UUID
from sqlalchemy_utils import URLType
from sqlalchemy.orm import relationship, Mapped 
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, mapped_column, backref
import os

from typing import List


from typing import Optional

from sqlalchemy import UniqueConstraint

Base = declarative_base()

subsumption = Table(
    'subsumption', Base.metadata,
    Column('sub_id', Integer, ForeignKey('Item.id'), index=True),
    Column('subOf_id', Integer, ForeignKey('Item.id')),
    UniqueConstraint('sub_id', 'subOf_id', name='subsumption'))




class Item(Base):
    __tablename__ = "Item"
    id = Column(Integer, primary_key = True, autoincrement=True)
    uri = Column(URLType, index=True)
    title = Column(String, default="")
    description = Column(String, default="")
    type = Column(String, nullable=False)
    prev_id = mapped_column(Integer, ForeignKey('Item.id'))
    next = relationship("Item", uselist = False, backref=backref("prev", remote_side=[id]))

    def __init__(self, *args, **kwargs):
        self.type = self.__class__.__tablename__
        super().__init__(*args, **kwargs)

    def commit_on(self, session):
        if not self.prev_id:
            last = session.query(Item).filter(Item.uri == self.uri).order_by(Item.id.desc()).first()
            if last:
                self.prev_id = last.id
        session.add(self)
        session.commit()

    @staticmethod
    def snapshot(session):
        return session.query(Item).filter(Item.next == None)

    
    def __repr__(self):
        return '<%s(title=|%s|)>' % (self.__class__.__name__, self.title)
"""
membership = Table(
    'membership', Base.metadata,
    Column('prop_id', Integer, ForeignKey('Property.id'), index=True),
    Column('comp_id', Integer, ForeignKey('Component.id')))
    #UniqueConstraint('prop_id', 'comp_id', name='membership'))

"""
class Property(Item):
    __tablename__ = "Property"
    __mapper_args__ = {
        'polymorphic_identity': 'Property',
        'polymorphic_on': 'type'
    }
    id = Column(None, ForeignKey('Item.id'), primary_key=True)
    datatype = Column(String, nullable = True)

    def add_comp(self, comp):
        comp.add_prop(self)



class Component(Item):
    """
    Components only ever add subs. There is no way to remove subs. This is to ensure that versions always 
    remain compatible. Also, it screws with property removal. 
    """
    __tablename__ = "Component"
    __mapper_args__ = {
        'polymorphic_identity': 'Component',
        'polymorphic_on': 'type'
    }
    id = Column(None, ForeignKey('Item.id'), primary_key=True)
    subs = relationship('Component',
                           secondary=subsumption,
                           primaryjoin= id==subsumption.c.sub_id,
                           secondaryjoin= id==subsumption.c.subOf_id, backref=backref("subOf") )
    properties = relationship('Property',
                           secondary=membership,
                           primaryjoin= id==membership.c.comp_id,
                           secondaryjoin=Property.id==membership.c.prop_id, backref=backref("components"))
    def add_sub(self, sub):
        if sub not in self.subs:
            self.subs.append(sub)   # irrefleivity
        for prop in sub.properties:
            self.add_prop(prop)
        for subsub in sub.subs:
            #subsub.add_sup(self)         # transivitiy
            self.add_sub(subsub)

    def add_sup(self, sup):
        sup.add_sub(self)


        

    def add_prop(self, prop):
        if prop not in self.properties:
            self.properties.append(prop)
        for sup in self.subOf:
            sup.add_prop(prop)
    
    def add_comp(self, comp):
        comp.add_prop(self)


    def remove_sub(self, sub):
        for subsub in self.subs:
            subsub.remove_sub(sub)
        if sub in self.subs:
            self.subs.remove(sub)


    def remove(self):
        """
        A Component can only be removed if it is no subOf another Component
        """
        if self.subOf:
            raise Exception("Only allowed for Components without subOf")
        for prop in self.properties:
            prop.components.remove(self)
        for sub in self.subs:
            self.remove_sub(sub)



            




Base.metadata.create_all(bind=engine)

items = [Item(uri="http://foo.com/"), Item(uri="http://bar.com/"), Item(uri="http://foo.com/", title="this one is new")]

person = Component(title="person")
faculty = Component(title="faculty")
student = Component(title="student")
ta = Component(title="ta")

p1 = Property(title="p1", datatype="string")
p2 = Property(title="p2", datatype="string")




"""

person.add_sub(faculty)
person.add_sub(student)
faculty.add_sub(ta)
student.add_sub(ta)
"""


ta.add_sup(student)
ta.add_sup(faculty)
student.add_sup(person)
faculty.add_sup(person)



ta.add_prop(p1)

faculty.add_prop(p2)
session = SessionLocal()


session.add_all([person, faculty, student, ta])
session.add_all([p1, p2])
session.commit()

for item in items:
    item.commit_on(session)

