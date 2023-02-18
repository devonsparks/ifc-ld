from sqlalchemy import Table, Column, ForeignKey, Integer, String, CheckConstraint, UUID, Boolean
from sqlalchemy_utils import URLType
from sqlalchemy.orm import relationship, Mapped 
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, mapped_column, backref
import os



from sqlalchemy import UniqueConstraint

engine=create_engine('sqlite://',echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()




class Item(Base):
    __tablename__ = "Item"
    id = Column(Integer, primary_key = True, autoincrement=True)
    uri = Column(URLType, index=True)
    title = Column(String, default="")
    type = Column(String, nullable=False)
    prev_id = mapped_column(Integer, ForeignKey('Item.id'))
    next = relationship("Item", uselist = False, foreign_keys="[Item.prev_id]", backref=backref("prev", remote_side=[id]))
    pred_id = mapped_column(Integer, ForeignKey('Item.id'))
    succ = relationship("Item", uselist = False, foreign_keys="[Item.pred_id]", backref=backref("pred", remote_side=[id]))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = self.__class__.__tablename__
        

    def post(self, session):
        pred = session.query(Item).filter(Item.uri == self.uri).order_by(Item.id.desc()).first()
        if pred:
            self.pred_id = pred.id
        session.add(self)
        session.flush()  # generate auto-id
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
        return '<%s(id=|%d|, uri=|%s|, title=|%s|)>' % (self.__class__.__name__, self.id, self.uri, self.title)

component_property = Table(
    'component_property', Base.metadata,
    Column('prop_id', Integer, ForeignKey('Property.id'), index=True),
    Column('comp_id', Integer, ForeignKey('Component.id'), index=True),
    UniqueConstraint('prop_id', 'comp_id', name='component_property'))

state_property = Table(
    'state_property', Base.metadata,
    Column('state_id', Integer, ForeignKey('State.id'), index=True),
    Column('prop_id', Integer, ForeignKey('Property.id')),
    UniqueConstraint('state_id', 'prop_id', name='state_property'))

state_component = Table(
    'state_component', Base.metadata,
    Column('state_id', Integer, ForeignKey('State.id'), index=True),
    Column('comp_id', Integer, ForeignKey('Component.id')),
    UniqueConstraint('state_id', 'comp_id', name='state_component'))


class Property(Item):
    __tablename__ = "Property"
    __mapper_args__ = {
        'polymorphic_identity': 'Property',
    }
    id = Column(None, ForeignKey('Item.id'), primary_key=True)
    required = Column(Boolean, default = False)

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
        for prop in Property.current(session):
            self.properties.append(prop)
        for comp in Component.current(session):
            self.components.append(comp)

    def _compute_version(self, session):
        if not self.prev:
            self.major_version = 0
            return


Base.metadata.create_all(bind=engine)

items = [
    Property(uri="http://schema.org/age", required=True), 
    Property(uri="http://foaf.org/friend"), 
    Component(uri="http://ifc.org/Wall"), 
    State(), 
    Property(uri="http://schema.org/age", title="age-v2"),  
    Component(uri="http://ifc.org/Slab"),
    Property(uri="http://schema.org/age", title="age-v3", required=True), 
    Component(uri="http://ifc.org/Wall"), State()
]



session = SessionLocal()

stack = session
for item in items:
    item.post(session)




for p in Property.current(session):
    Component.top(session).properties.append(p)

session.commit()


for i in session.query(Item).order_by(Item.id.desc()):
    print(i)
