# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT


from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy_utils import URLType
from sqlalchemy.orm import relationship, backref, mapped_column
from database import Base

from uuid_extensions import uuid7str

def new_id():
    return uuid7str()

class Item(Base):
    __tablename__ = "Item"
    __apiname__ = "items"
    id = Column(String, primary_key=True, default=new_id)
    uri = Column(URLType, index=True)
    title = Column(String, default="")
    description = Column(String, default="")
    type = Column(String, nullable=False)
    prev_id = mapped_column(None, ForeignKey('Item.id'), default=None)
    next = relationship("Item", uselist=False, foreign_keys="[Item.prev_id]", backref=backref(
        "prev", remote_side=[id]))
    pred_id = mapped_column(None, ForeignKey('Item.id'), default=None)
    succ = relationship("Item", uselist=False, foreign_keys="[Item.pred_id]", backref=backref(
        "pred", remote_side=[id]))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = self.__class__.__tablename__
        self.id = new_id()
    @classmethod
    def get(cls, session, id):
        return session.get(cls, id)

    def post(self, session):
        session.add(self)
        session.flush()  # generate auto-id
        if not self.uri:
            self.uri = "/{type}/{id}".format(type = self.__class__.__apiname__, id=self.id)
        pred = session.query(Item).filter(Item.uri == self.uri).filter(
            Item.id < self.id).order_by(Item.id.desc()).first()
        if pred:
            self.pred_id = pred.id
        if self.id:  # FIXME: always True after autocrement change?
            prev = session.query(Item).filter(Item.type == self.type).filter(
                Item.id < self.id).order_by(Item.id.desc()).first()
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
    def top(cls, session):
        return session.query(cls).filter(cls.next == None).order_by(cls.id.desc()).first()

    @classmethod
    def current(cls, session):
        return session.query(cls).filter(cls.succ == None).all()

    def compatible_with(self, other):
        return type(self) == type(other) and self.uri == other.uri

    def __repr__(self):
        return '<%s(id=|%s|, uri=|%s|, title=|%s|)>' % (self.__class__.__name__, self.id or -1, self.uri or "", self.title or "")


class Property(Item):
    __tablename__ = "Property"
    __apiname__ = "properties"
    __mapper_args__ = {
        'polymorphic_identity': 'Property',
    }
    id = Column(None, ForeignKey('Item.id'), primary_key=True)
    required = Column(Boolean, default=False)
    datatype = Column(URLType)
    lower = Column(Integer, default=0)
    upper = Column(Integer, default=-1)
    ordered = Column(Boolean, default=False)
    # opposite = Column(None, ForeignKey('Property.id'), nullable = True)

    related_components = relationship("ComponentPropertyRelation",
                                      back_populates="target")

    related_states = relationship("StatePropertyRelation",
                                      back_populates="target")


class StringProperty(Property):
    __tablename__ = "StringProperty"
    __mapper_args__ = {
        'polymorphic_identity': 'StringProperty',
    }
    id = Column(None, ForeignKey('Property.id'), primary_key=True)
    pattern = Column(String, default="*.")

class ValueRangeProperty(Property):
    __tablename__ = "ValueRangeProperty"
    __mapper_args__ = {
        'polymorphic_identity': 'ValueRangeProperty',
    }
    id = Column(None, ForeignKey('Property.id'), primary_key=True)
    minimum = Column(String, default = None)
    maximum = Column(String, default = None)

class Component(Item):
    __tablename__ = "Component"
    __apiname__ = "components"
    __mapper_args__ = {
        'polymorphic_identity': 'Component'
    }
    id = Column(None, ForeignKey('Item.id'), primary_key=True)

    related_subcomponents = relationship("ComponentComponentRelation",
                                         back_populates="source",
                                         foreign_keys="[ComponentComponentRelation.source_id]")

    related_supercomponents = relationship("ComponentComponentRelation",
                                           back_populates="target",
                                           foreign_keys="[ComponentComponentRelation.target_id]")

    related_properties = relationship("ComponentPropertyRelation",
                                      back_populates="source")

    related_states = relationship("StateComponentRelation",
                                      back_populates="target")


    def delete(self, session):
        for prop in self.properties:
            prop.components.remove(self)
        super().delete(session)


class State(Item):
    __tablename__ = "State"
    __apiname__ = "states"
    __mapper_args__ = {
        'polymorphic_identity': 'State',
    }
    id = Column(None, ForeignKey('Item.id'), primary_key=True)
    property_id = Column(None, ForeignKey('Property.id'))
    component_id = Column(None, ForeignKey('Component.id'))
    top_property = relationship("Property", foreign_keys="[State.property_id]")
    top_component = relationship("Component", foreign_keys="[State.component_id]")

    related_properties = relationship("StatePropertyRelation",
                                      back_populates="source")

    related_components = relationship("StateComponentRelation",
                                      back_populates="source")

    def post(self, session):
        self.top_property = Property.top(session)
        self.top_component = Component.top(session)
        self._freeze(session)
        super().post(session)

    def _freeze(self, session):
        session.flush()
        for prop in Property.current(session):
            StatePropertyRelation(source = self, target = prop).post(session)
        for comp in Component.current(session):
            StateComponentRelation(source = self, target = comp).post(session)
            


class Relation:
    @classmethod
    def get(cls, session, source_id, target_id):
        return session.get(cls, (source_id, target_id))

    def post(self, db):
        # db.flush()
        link = self.__class__.get(db, self.source.id, self.target.id)
        if link:
            print("incrementing...")
            link.refs = link.refs + 1
        else:
            print("adding new")
            db.add(self)
            db.commit()

    def delete(self, db):
        #link = db.get(cls, (source.id, target.id))
        link = self.__class__.get(db, self.source.id, self.target.id)
        if link:
            if link.refs == 1:
                print("deleting...")
                db.delete(link)
                db.commit()
            else:
                print("decrementing...")
                link.refs = link.refs - 1
        else:
            raise Exception("No association between source and target")

    @classmethod
    def create(cls, source_cls, target_cls, source_backref, target_backref):
        rel_name = "{source}{target}Relation".format(
            source=source_cls, target=target_cls)
        table_name = "{source}_{target}_relation".format(
            source=source_cls, target=target_cls)
        source_id = Column(String, ForeignKey(
            "{source_cls}.id".format(source_cls=source_cls)), primary_key=True)
        target_id = Column(String, ForeignKey(
            "{target_cls}.id".format(target_cls=target_cls)), primary_key=True)
        refs = Column(Integer, default=1)
        source = relationship(source_cls,
                              back_populates=source_backref,
                              primaryjoin="{source_cls}.id == {relation}.source_id".format(source_cls=source_cls, relation=rel_name))
        target = relationship(target_cls,  back_populates=target_backref,
                              primaryjoin="{target_cls}.id == {relation}.target_id".format(target_cls=target_cls, relation=rel_name))

        return type(rel_name, (Base, Relation,), {"__tablename__": table_name,
                                                  "source": source, "target": target, "refs": refs,
                                                  "source_id": source_id, "target_id": target_id})



ComponentPropertyRelation = Relation.create(
    "Component", "Property", "related_properties", "related_components")

ComponentComponentRelation = Relation.create(
    "Component", "Component", "related_subcomponents", "related_supercomponents")

StateComponentRelation = Relation.create(
    "State", "Component", "related_components", "related_states")

StatePropertyRelation = Relation.create(
    "State", "Property", "related_properties", "related_states")




# /{source_type}/{source_id}/links/{target_type}/{target_id}
