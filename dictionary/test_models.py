from unittest import TestCase

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base
from models import Property, Component, Model, State, Item

from database import Base


class TestBase(TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = self.Session()
        Base.metadata.create_all(self.engine)
    
    def tearDown(self):
        Base.metadata.drop_all(self.engine)


class TestItem(TestBase):

    def test_assignment(self):
        p1 = Property(uri="http://schema.org/length", required=True)
        c1 = Component(uri="http://ifc.org/Slab")
        m1 = Model()
        m1.components.append(c1)
        m1.properties.append(p1)
        c1.properties.append(p1)
        p1.post(self.session)
        c1.post(self.session)
        m1.post(self.session)
        s = State()
        s.post(self.session)

        # Property Components
        self.assertTrue([c1] == self.session.get(Property, p1.id).components)

        # Component Properties
        self.assertTrue([p1] == self.session.get(Component, c1.id).properties)

        # Property Models
        self.assertTrue([m1] == self.session.get(Property, p1.id).models)

        # Model Properties
        self.assertTrue([p1] == self.session.get(Model, m1.id).properties)

        # Model Components
        self.assertTrue([c1] == self.session.get(Model, m1.id).components)

         # Component Models
        self.assertTrue([m1] == self.session.get(Component, c1.id).models)

        # Check State
        self.assertTrue([p1] == self.session.get(State, s.id).properties)
        self.assertTrue([c1] == self.session.get(State, s.id).components)
        self.assertTrue([m1] == self.session.get(State, s.id).models)

    def test_top(self):
        i1 = Item(title="v1")
        i2 = Item(title="v2")
        i3 = Item(title="v3")

        i1.post(self.session)
        self.assertTrue(Item.top(self.session) == i1)
        i2.post(self.session)
        self.assertTrue(Item.top(self.session) == i2)
        i3.post(self.session)
        self.assertTrue(Item.top(self.session) == i3)

    def test_current(self):
        i1 = Item(title="v1", uri="http://v1.com/")
        i2 = Item(title="v2", uri="http://v2.com/")
        i11 = Item(title="v11", uri="http://v1.com/")
        
        i1.post(self.session)
        self.assertTrue(set(Item.current(self.session)) == set([i1]))
        i2.post(self.session)
        self.assertTrue(set(Item.current(self.session)) == set([i1, i2]))
        i11.post(self.session)
        self.assertTrue(set(Item.current(self.session)) == set([i11, i2]))
        
    def test_models(self):
        items = [
        Property(uri="http://schema.org/length", required=True), 
        Property(uri="http://schema.org/material", required=True), 
        Component(uri="http://ifc.org/Slab"),
        Component(uri="http://ifc.org/Wall"), 
        ]

        m = Model(title="First Model")
        m.properties.append(items[0])
        m.properties.append(items[1])
        m.components.append(items[2])
        m.components.append(items[3])

        items.append(m)

        items.append(State())

        p1 = Property(uri="http://schema.org/material", required=False)
        p2 = Property(uri="http://schema.org/size", required=False)
        foo = Component(uri="http://ifc.org/Foo")
        items.append(p1)
        items.append(p2)
        
        items.append(foo)
        items.append(State())

        for item in items:
            item.post(self.session)

        self.assertTrue(self.session.get(Property, 1).uri == "http://schema.org/length")