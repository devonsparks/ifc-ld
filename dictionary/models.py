from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, CheckConstraint
from sqlalchemy_utils import URLType
from sqlalchemy.orm import relationship
from database import Base


class Resource(Base):
    __tablename__ = "Resource"
    id = Column(URLType, primary_key=True, index=True)
    title = Column(String, default="")
    description = Column(String, default="")
    type = Column(String, nullable=False)

    def __init__(self, *args, **kwargs):
        self.type = self.__class__.__tablename__
        super().__init__(*args, **kwargs)


class Association(Base):
    __abstract__ = True
    key = Column(String, nullable=False)
    required = Column(Boolean, default=True)


class Type(Resource):
    __tablename__ = "Type"
    id = Column(None, ForeignKey('Resource.id'), primary_key=True)
    component_assignments = relationship(
        "ComponentTypeAssignment", back_populates="type")
    __mapper_args__ = {
        'polymorphic_identity': 'Type',
        'polymorphic_on': 'type'
    }


class Component(Resource):
    __tablename__ = "Component"
    id = Column(None, ForeignKey('Resource.id'), primary_key=True)
    property_assignments = relationship(
        "PropertyComponentAssignment", back_populates="component")
    type_assignments = relationship(
        "ComponentTypeAssignment", back_populates="component")
    __mapper_args__ = {
        'polymorphic_identity': 'Component',
        'polymorphic_on': 'type'
    }


class Property(Resource):
    __tablename__ = "Property"
    __mapper_args__ = {
        'polymorphic_identity': 'Property',
        'polymorphic_on': 'type'
    }
    id = Column(None, ForeignKey('Resource.id'), primary_key=True)
    datatype = Column(URLType)
    lower = Column(Integer, CheckConstraint("lower > 0"), default=1)
    upper = Column(Integer, CheckConstraint(
        "upper = -1 OR upper > 1"), default=-1)
    ordered = Column(Boolean, default=True)
    component_assignments = relationship(
        "PropertyComponentAssignment", back_populates="property")


class StringProperty(Property):
    __tablename__ = "StringProperty"
    __mapper_args__ = {
        'polymorphic_identity': 'StringProperty',
        'polymorphic_on': 'type'
    }

    id = Column(None, ForeignKey('Property.id'), primary_key=True)
    pattern = Column(String, default="*")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datatype = "http://www.w3.org/2001/XMLSchema#string"



class URIProperty(Property):
    __tablename__ = "URIProperty"

    id = Column(None, ForeignKey('Property.id'), primary_key=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datatype = "http://www.w3.org/2001/XMLSchema#anyURI"



class ValueRangeProperty(Property):
    __tablename__ = "ValueRangeProperty"
    __mapper_args__ = {
        'polymorphic_identity': 'ValueRangeProperty',
        'polymorphic_on': 'type'
    }
    id = Column(None, ForeignKey('Property.id'), primary_key=True)
    minimum = Column(Integer, default=0, nullable=False)
    maximum = Column(Integer, default=256, nullable=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datatype = "http://www.w3.org/2001/XMLSchema#double"



class ConstantValueProperty(ValueRangeProperty):
    __tablename__ = "ConstantValueProperty"
    id = Column(None, ForeignKey('ValueRangeProperty.id'), primary_key=True)
    value = Column(Integer, default=0, nullable=False)
    __mapper_args__ = {'polymorphic_identity': 'ConstantValueProperty'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.minimum = self.value
        self.maximum = self.value



class PropertyComponentAssignment(Association):
    __tablename__ = "PropertyComponentAssignment"
    property_id = Column(URLType, ForeignKey("Property.id"), primary_key=True)
    component_id = Column(URLType, ForeignKey(
        "Component.id"), primary_key=True)
    property = relationship("Property", back_populates="component_assignments")
    component = relationship(
        "Component", back_populates="property_assignments")


class ComponentTypeAssignment(Association):
    __tablename__ = "ComponentTypeAssignment"
    component_id = Column(URLType, ForeignKey(
        "Component.id"), primary_key=True)
    type_id = Column(URLType, ForeignKey("Type.id"), primary_key=True)
    component = relationship("Component", back_populates="type_assignments")
    type = relationship("Type", back_populates="component_assignments")


