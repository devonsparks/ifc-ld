# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, UniqueConstraint, Table, event
from sqlalchemy_utils import URLType
from sqlalchemy.orm import relationship, backref, mapped_column
from database import Base



class Item(Base):
    __tablename__ = "Item"
    id = Column(Integer, primary_key = True, autoincrement=True)
    uri = Column(URLType, index=True)
    title = Column(String, default="")
    description = Column(String, default="")
    type = Column(String, nullable=False)
    prev_id = mapped_column(Integer, ForeignKey('Item.id'), default=None)
    next = relationship("Item", uselist = False, foreign_keys="[Item.prev_id]", backref=backref("prev", remote_side=[id]))
    pred_id = mapped_column(Integer, ForeignKey('Item.id'), default=None)
    succ = relationship("Item", uselist = False, foreign_keys="[Item.pred_id]", backref=backref("pred", remote_side=[id]))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = self.__class__.__tablename__
        

    def post(self, session):
        session.add(self)
        session.flush()  # generate auto-id
        if not self.uri:
            self.uri = "/{type}/{id}".format(type=self.type, id=self.id)
        pred = session.query(Item).filter(Item.uri == self.uri).filter(Item.id < self.id).order_by(Item.id.desc()).first()
        if pred:
            self.pred_id = pred.id
        if self.id > 1:
            prev = session.query(Item).filter(Item.type == self.type).filter(Item.id < self.id).order_by(Item.id.desc()).first()
            if prev:
                self.prev_id = prev.id
        session.commit()


    def delete(self, session):
        if self.next:
            self.next.prev_id = self.prev_id
        if self.succ:
            self.succ.pred_id = self.pred_id
        self.pred_id = None
        self.prev_id = None
        session.delete(self)
        session.commit()

    @classmethod
    def get(cls, session, id):
        return session.get(cls, id)

    @classmethod
    def top(cls, session):
        return session.query(cls).filter(cls.next == None).order_by(cls.id.desc()).first()

    @classmethod
    def current(cls, session):
        return session.query(cls).filter(cls.succ == None).all()

    def compatible_with(self, other):
        return type(self) == type(other) and self.uri == other.uri
    
    def __repr__(self):
        return '<%s(id=|%d|, uri=|%s|, title=|%s|)>' % (self.__class__.__name__, self.id or -1, self.uri or "", self.title or "")


component_property = Table(
    'component_property', Base.metadata,
    Column('prop_id', Integer, ForeignKey('Property.id'), index=True),
    Column('comp_id', Integer, ForeignKey('Component.id'), index=True),
    Column('refs', Integer, default = 0),
    UniqueConstraint('prop_id', 'comp_id', name='component_property_constraint'))

state_property = Table(
    'state_property', Base.metadata,
    Column('state_id', Integer, ForeignKey('State.id'), index=True),
    Column('prop_id', Integer, ForeignKey('Property.id')),
    UniqueConstraint('state_id', 'prop_id', name='state_property_constraint'))

state_component = Table(
    'state_component', Base.metadata,
    Column('state_id', Integer, ForeignKey('State.id'), index=True),
    Column('comp_id', Integer, ForeignKey('Component.id')),
    UniqueConstraint('state_id', 'comp_id', name='state_component_constraint'))

component_subs = Table(
    'component_subs', Base.metadata,
    Column('sub_id', Integer, ForeignKey('Component.id'), index=True),
    Column('subOf_id', Integer, ForeignKey('Component.id')),
    UniqueConstraint('sub_id', 'subOf_id', name='component_subs_constraint'))

class Property(Item):
    __tablename__ = "Property"
    __mapper_args__ = {
        'polymorphic_identity': 'Property',
    }
    id = Column(None, ForeignKey('Item.id'), primary_key=True)
    required = Column(Boolean, default = False)
    datatype = Column(URLType)
    lower = Column(Integer, default = 0)
    upper = Column(Integer, default = -1)
    ordered = Column(Boolean, default = False)
    #opposite = Column(None, ForeignKey('Property.id'), nullable = True)

    def delete(self, session):
        for comp in self.components:
            comp.properties.remove(self)
        super().delete(session)


    def compatible_with(self, other):
        if not super().compatible_with(other):
            return False
        if other.required == self.required:
            return True
        else:
            if other.id < self.id:
                if other.required and not self.required:
                    return True
                else:
                    return False
            else:
                if other.required and not self.required:
                    return False
                else:
                    return True
                

class Component(Item):
    __tablename__ = "Component"
    __mapper_args__ = {
        'polymorphic_identity': 'Component',
    }
    id = Column(None, ForeignKey('Item.id'), primary_key=True)

    subcomponents = relationship('Component',
                           secondary=component_subs,
                           primaryjoin= id==component_subs.c.sub_id,
                           secondaryjoin= id==component_subs.c.subOf_id, backref=backref("subComponentOf"))

    properties = relationship('Property',
                           secondary=component_property,
                           primaryjoin= id==component_property.c.comp_id,
                           secondaryjoin=Property.id==component_property.c.prop_id, backref=backref("components"))
    
    def delete(self, session):
        for prop in self.properties:
            prop.components.remove(self)
        super().delete(session)

    def compatible_with(self, other):
        if not super().compatible_with(other):
            return False
        return set(other.properties).issubset(self.properties)



class State(Item):
    __tablename__ = "State"
    __mapper_args__ = {
        'polymorphic_identity': 'State',
    }
    id = Column(None, ForeignKey('Item.id'), primary_key=True)
    major_version = Column(Integer, default=0)
    minor_version = Column(Integer, default=0)
    prop_id = Column(Integer, ForeignKey('Property.id'))
    comp_id = Column(Integer, ForeignKey('Component.id'))
    top_property = relationship("Property", foreign_keys="[State.prop_id]")
    top_component = relationship("Component", foreign_keys="[State.comp_id]")

    properties = relationship('Property',
                  secondary=state_property,
                    primaryjoin= id==state_property.c.state_id,
                    secondaryjoin=Property.id==state_property.c.prop_id, backref=backref("states"))

    components = relationship('Component',
                  secondary=state_component,
                    primaryjoin= id==state_component.c.state_id,
                    secondaryjoin=Component.id==state_component.c.comp_id, backref=backref("states"))

    def post(self, session):
        self.top_property = Property.top(session)
        self.top_component = Component.top(session)
        self._freeze(session)
        super().post(session)

    def _freeze(self, session):
        session.flush()
        for prop in Property.current(session):
            self.properties.append(prop)
        for comp in Component.current(session):
            self.components.append(comp)

    def _compute_version(self, session):
        if not self.prev:
            self.major_version = 0
            return




@event.listens_for(Component.subcomponents, 'append', propagate=True)
def on_subcomponent_add(comp, sub, _):
    for prop in sub.properties:
        comp.properties.append(prop)

@event.listens_for(Component.subcomponents, 'remove', propagate=True)
def on_subcomponent_remove(comp, sub, _):
    pass