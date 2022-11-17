# SPDX-License-Identifier: LGPL-3.0-or-later

from uuid import uuid4
import json
from collections import defaultdict
from abc import abstractmethod
import inspect

class bcolors:
	HEADER = '\033[95m'
	OKBLUE = '\033[94m'
	OKCYAN = '\033[96m'
	OKGREEN = '\033[92m'
	WARNING = '\033[93m'
	FAIL = '\033[91m'
	ENDC = '\033[0m'
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'

def warn(msg):
	print(f"{bcolors.WARNING}Warning:{bcolors.ENDC} %s"%msg)


class Repository:
	"""
	A Repository represents a backing store for a collection of ECs.
 
	Concrete subclasses implement the core methods of Repository, which
	intentionally mirror standard HTTP verbs, including idempotency expectations.
	"""
	def __init__(self, *constructors):
		assert len(constructors) > 0
		assert all([inspect.isclass(cls) for cls in constructors])
		self.constructors = constructors
		
	def add_constructors(self, *constructors):
		self.constructors = list(constructors) + self.constructors
	
	def constructor_for(self, bindings):
		"Returns the first constructor that can process :bindings"
		for constructor in self.constructors:
			if constructor.can_parse(bindings):
				return constructor(self, bindings)
	
	def new_id(self):
		return str(uuid4())

	@abstractmethod
	def has_id(self, id) -> bool:
		"""
		Returns a boolean whether the Repository contains id. 
		"""

	@abstractmethod
	def create(self):
		"""
		Generate a new set of bindings with a new (randomly generated) id.

		In a HTTP implementation, maps to POST /ecs
		"""
	
	@abstractmethod
	def get(self, id):
		"""
		Fetches a set of bindings by id.

		In an HTTP implementation, maps to GET /ecs/:id
		"""

	@abstractmethod
	def put(self, bindings):
		"""
		Completely replace a set of bindings.

		In an HTTP implementation, maps to PUT /ecs/:id
		where :id is retrieved from the bindings.

		If the bindings contain no :id key, one is generated automatically.
		"""


class MemRepository(Repository):
	"An in-memory Repository implementation."
	def __init__(self, *constructors):
		super().__init__(*constructors)
		self.db = {}
	
	def has_id(self, id):
		return bool(self.db.get(id))

	def create(self):
		id = self.new_id() 
		self.db[id] = {"id":id}
		return self.db[id].get("id")

	def get(self, id):
		return self.db.get(id)
	
	def put(self, bindings):
		if not bindings.get("id"):
			bindings["id"] = self.new_id()
		kvs = {}
		for (k, v) in bindings.items():
			kvs[k] = self.put(v) if isinstance(v, dict) else v
		self.db[bindings.get("id")] = kvs
		return bindings.get("id")


class EC:
	"""
	An EC is a set of key-value pairs, along with methods 
	to that allow clients to search for, annotate, and extend those 
	pairs. 

	EC acts like JSON object literals with additional behavior, 
	including differential inheritance. 
	"""
	ParentSymbol = "*"
	def __init__(self, repo, bindings = {}):
		self.repo = repo
		self.bindings = self.repo.get(self.repo.put(bindings))
		assert self.bindings["id"]
	
	def to_json(self):
		"Retrieve the underlying JSON (dictionary) bindings."
		return self.bindings

	def cls(self):
		"Helper to fetch the class of the current instance"
		return self.__class__
	
	def has_parent(self):
		return self.cls().ParentSymbol in self.bindings

	def parent(self):
		"Return the parent EC of this EC"
		if self.has_parent():
			return self.get(self.cls().ParentSymbol)

	@classmethod
	def can_parse(self, bindings):
		"""
		Answers whether this class can parse a given set of bindings.
		Used for finding the appropriate class constructor for a set of bindings.
		"""
		return True

	def update(self, bindings):
		"""
		Low-level call to manually update my key-value bindings.

		This method sidesteps all higher-level integrity checks, so should
		be used sparingly. Prefer declare() and let(). 
		"""
		self.bindings = self.repo.get(self.repo.put({**self.bindings, **bindings}))
		return self

	def get(self, key):
		"""
		Given a key, searches the current EC for a matching value.

			If the value is found in the current set of bindings:
				If that value is an identifier registered in the Repository: 
					the identifier is dereferenced and its EC returned. 
				Otherwise:
					the value is returned as-is

			Otherwise: 
				search is repeated in the EC that is this EC's parent.

			An ValueError is raised if no key can be found in the EC or 
			any of its parents. 

		The recursive searching through EC supports simple, differential 
		inheritance, where EC can override values  set by their parent
		EC. 
		"""
		if key in self.bindings:
			value = self.bindings[key]
			if isinstance(value, list):
				return [self.repo.constructor_for(self.repo.get(id)) for id in value]
			elif self.repo.has_id(value) and not key == "id":
				return self.repo.constructor_for(self.repo.get(value))
			else:
				return value
		elif self.has_parent():
			return self.parent().get(key)
		else: 
			raise ValueError("%s is not defined"%(key,))

	def get_all(self, key):
		"Returns _all_ results of calling get(key) through the parent chain."
		try:
			yield self.get(key)
			yield from self.parent().get_all(key)
		except ValueError:
			return

	def resolve(self, key, excludes = []) -> dict:
		"""
		Returns a dict representing :key,
		including all embedded key-value pairs,
		including resolution of linked ECs.
		"""
		infdict = lambda: defaultdict(infdict)
		return self._resolve(key, infdict(), excludes)
	
	def _resolve(self, key, result, excluded_keys = []):
		"The helper method of resolve(), handling recursive calls."
		here = self.get(key)
		if not isinstance(here, self.cls()):
			return here
		else:
			for k in here.bindings:
				if k in excluded_keys:
					continue
				result[k] = here._resolve(k, result[k], excluded_keys)
		return dict(result)

	def fork(self, bindings = None):
		"Creates a new EC object, with the current EC as its parent."
		bindings = bindings or dict()
		bindings[self.cls().ParentSymbol] = self.bindings["id"]
		return self.repo.constructor_for(bindings)
	
	def declare(self, key, uri = None, type = None):
		"""
		Declares the  meaning of a key by linking it to a URI definition 
		and optionally a type URI (used for keys representing literals).

		Under the hood, this method populates the JSON-LD @context of the
		EC object.
		"""
		if not "@context" in self.bindings:
			self.update({"@context":{}})#, "@type":"Component"})
		if not uri: 
			uri = key
			type = "@vocab"
		if not type:
			type = "@id"
		self.get("@context").update({key:{"@id":uri, "@type":type}})
		return self

	def redeclare(self, key):
		"""
		Copies an existing declaration into the local EC's @context.
		"""
		decl = self.declaration_of(key)
		if not decl:
			raise ValueError("Declaration of key not found. Use declare(). ")
		self.get("@context").update({key:decl.bindings.copy()})

	def declaration_of(self, key):
		"""
		Returns the declaration (@context entry) for a given key. 
		"""
		for ctx in self.get_all("@context"):
			if key in ctx.bindings:
				return ctx.get(key)
		
	def let(self, key, value):
		"""
		Primary method for updating a key-value pair in a EC. 
		Value can be either a EC or literal. 
		Setting behavior is different in each case.

		let() checks that that the provided :key has been declared()
		before it's set, and issues a warning otherwise.
		"""
		#key = env.get(key)
		if not self.declaration_of(key):
			warn("Unable to find declaration for key %s. Use delcare() to define this key. "%(key))
		if self.repo.has_id(self.bindings.get(key)): 	# already binds singleton id? 
				return self.update({key: [value.get("id")] + [self.bindings[key]]})
		elif isinstance(self.bindings.get(key), list):	# already binds list of ids?
			return self.update({key: [value.get("id")] + self.bindings[key]})
		elif isinstance(value, self.cls()):
			return self.update({key: value.get("id")})
		else:
			return self.update({key: value})

	def keys(self, recur = False):
		"Get all keys of the EC, with optional recursion to parent EC."
		if not recur:
			return set(self.bindings.keys())
		else:
			parent = self.parent()
			return self.keys(False).union((parent and parent.keys(True)) or set([]))

	def snapshot(self):
		"""
		Return a complete (dict) snapshot of the current EC by
		resolve()-ing all keys. 
		"""
		return {key:self.resolve(key) for key in self.keys(True)}

	def transfer(self, repo):
		"""
		Replicates this EC, along with all of its linked EC,
		in the provided Repository. 
		"""
		return repo.put(self.snapshot())

	def __repr__(self):
		return f"{bcolors.OKGREEN}%s{bcolors.ENDC}(%s)"%(self.__class__.__name__, json.dumps(self.to_json(), indent=4))


