from uuid_extensions import uuid7str




class Entry:

    @classmethod
    def new_id(cls):
        return uuid7str()

    def __init__(self, uri, base_uri):
        self.id = self.__class__.new_id()
        self.uri = uri # equivalent to a base class ID
        self.base_uri = base_uri
        self.prev = None
        self.next = None
        self.predecessor = None
        self.successor = None

    def __repr__(self):
        return "(%s)"%(self.uri)

class Class(Entry):
    def __init__(self, uri, base)

class Property(Entry):
    pass

class Dictionary:
    def __init__(self):
        self.top = None

    def insert(self, entry):
        here = self.top
        while here:
            print("here:", here)
            if here.uri == entry.uri:
                print("match on ",here.uri)
                entry.predecessor = here
                assert not here.successor 
                here.successor = entry
                break
            here = here.prev
        entry.prev = self.top
        self.top = entry
        

    def lookup(self, uri):
        here = self.top
        while here:
            if here.uri == uri:
                return here
            here = here.prev
        raise Exception("Not found")



D = Dictionary()

wall = Entry("http://schema.org/wall")
slab = Entry("http://schema.org/slab")
D.insert(wall)
D.insert(slab)
D.insert(Entry("http://schema.org/wall"))

#D.lookup("http://schema.org/wall")