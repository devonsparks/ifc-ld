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
    __mapper_args__ = {
        "polymorphic_identity":"Item",
        "polymorphic_on":"type"
    }
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

    related_components = relationship("HasPropertyRelation",
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
    minimum = Column(Integer, default = 0)
    maximum = Column(Integer, default = -1)


class Component(Item):
    __tablename__ = "Component"
    __apiname__ = "components"
    __mapper_args__ = {
        'polymorphic_identity': 'Component'
    }
    id = Column(None, ForeignKey('Item.id'), primary_key=True)

    #related_subcomponents = relationship("HasSubComponentRelation",
    #                                     back_populates="source",
    #                                     foreign_keys="[HasSubComponentRelation.source_id]")

    #related_supercomponents = relationship("HasSubComponentRelation",
    #                                       back_populates="target",
    #                                       foreign_keys="[HasSubComponentRelation.target_id]")

    related_properties = relationship("HasPropertyRelation",
                                      back_populates="source")

    related_types = relationship("HasComponentRelation",
                                      back_populates="target")

    related_states = relationship("StateComponentRelation",
                                      back_populates="target")

    def delete(self, session):
        for prop in self.properties:
            prop.components.remove(self)
        super().delete(session)


class Type(Item):
    __tablename__ = "Type"
    __apiname__ = "types"
    __mapper_args__ = {
        'polymorphic_identity': 'Type',
    }
    id = Column(None, ForeignKey('Item.id'), primary_key=True)

    related_components = relationship("HasComponentRelation",
                                      back_populates="source")

    related_states = relationship("StateTypeRelation",
                                      back_populates="target")


class State(Item):
    __tablename__ = "State"
    __apiname__ = "states"
    __mapper_args__ = {
        'polymorphic_identity': 'State',
    }
    id = Column(None, ForeignKey('Item.id'), primary_key=True)
    property_id = Column(None, ForeignKey('Property.id'))
    component_id = Column(None, ForeignKey('Component.id'))
    type_id = Column(None, ForeignKey('Type.id'))
    top_property = relationship("Property", foreign_keys="[State.property_id]")
    top_component = relationship("Component", foreign_keys="[State.component_id]")
    top_type = relationship("Type", foreign_keys="[State.type_id]")

    related_properties = relationship("StatePropertyRelation",
                                      back_populates="source")

    related_components = relationship("StateComponentRelation",
                                      back_populates="source")

    related_types = relationship("StateTypeRelation",
                                      back_populates="source")

    def post(self, session):
        self.top_property = Property.top(session)
        self.top_component = Component.top(session)
        self.top_type = Type.top(session)
        self._freeze(session)
        super().post(session)

    def _freeze(self, session):
        session.flush()
        for prop in Property.current(session):
            StatePropertyRelation(source = self, target = prop).post(session)
        for comp in Component.current(session):
            StateComponentRelation(source = self, target = comp).post(session)
        for type in Type.current(session):
            StateTypeRelation(source = self, target = type).post(session)
            

class RefCountMixin:
    refs = Column(Integer, default=1)
    
class RelationMixin(RefCountMixin):
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

        return type(rel_name, (Base, RelationMixin,), {"__tablename__": table_name,
                                                  "source": source, "target": target, "refs": refs,
                                                  "source_id": source_id, "target_id": target_id})


class HasPropertyRelation(Base, RelationMixin, RefCountMixin):
    __tablename__="HasPropertyRelation"
    __apiname__ = "HasPropertyRelation"
    __mapper_args__ = {
        'polymorphic_identity': 'HasPropertyRelation',
    }
    source_id = Column(String, ForeignKey('Component.id'), primary_key=True)
    target_id = Column(String, ForeignKey('Property.id'), primary_key=True)
    source = relationship("Component", back_populates="related_properties")
    target = relationship("Property",  back_populates="related_components")


class HasComponentRelation(Base, RelationMixin, RefCountMixin):
    __tablename__="HasComponentRelation"
    __apiname__ = "HasComponentRelation"
    __mapper_args__ = {
        'polymorphic_identity': 'HasComponentRelation',
    }
    source_id = Column(String, ForeignKey('Type.id'), primary_key=True)
    target_id = Column(String, ForeignKey('Component.id'), primary_key=True)
    source = relationship("Type",
                              back_populates="related_components",
                              primaryjoin="Type.id == HasComponentRelation.source_id")
    target = relationship("Component",  back_populates="related_types",
                              primaryjoin="Component.id == HasComponentRelation.target_id")


"""

class HasSubComponentRelation(Base, RelationMixin, RefCountMixin):
    __tablename__="HasSubComponentRelation"
    __apiname__ = "HasSubComponentRelation"
    __mapper_args__ = {
        'polymorphic_identity': 'HasSubComponentRelation',
    }
    source_id = Column(String, ForeignKey('Component.id'), primary_key=True)
    target_id = Column(String, ForeignKey('Component.id'), primary_key=True)
    source = relationship("Component",
                              back_populates="related_subcomponents",
                              primaryjoin="Component.id == HasSubComponentRelation.source_id")
    target = relationship("Component",  back_populates="related_supercomponents",
                              primaryjoin="Component.id == HasSubComponentRelation.target_id")

    def post(self, db):
        super().post(db)
        print(self.target)
        print(self.target.related_properties)
        for related_prop in self.target.related_properties:
            print(related_prop.target)
            HasPropertyRelation(source=self.source, target=related_prop.target).post(db)
        db.commit()
"""
#HasPropertyRelation = RelationMixin.create(
#    "Component", "Property", "related_properties", "related_components")

#HasSubComponentRelation = RelationMixin.create(
#    "Component", "Component", "related_subcomponents", "related_supercomponents")

StateComponentRelation = RelationMixin.create(
    "State", "Component", "related_components", "related_states")

StatePropertyRelation = RelationMixin.create(
    "State", "Property", "related_properties", "related_states")

StateTypeRelation = RelationMixin.create(
    "State", "Type", "related_types", "related_states")


# /{source_type}/{source_id}/links/{target_type}/{target_id}
