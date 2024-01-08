# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.logger import logger
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import AnyUrl
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.orm import Session
from typing import Union
from models import Property, Component, Type, State
from models import StateComponentRelation, StatePropertyRelation, StateTypeRelation, HasPropertyRelation, HasComponentRelation

from database import Base, engine, get_db
import dtos
from enum import Enum

from presenters import present

def mime_types():
    return {
        200: {
            'content': {
                'application/json': {},
                'application/shacl+json': {},
                'application/ld+json': {},
                'application/schema+json': {},
                'text/html': {}
            },
        }
    }


def get_application():
    Base.metadata.create_all(bind=engine)
    app = FastAPI(title="Dictionary", version="0.0.1")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


def get(type, db: Session, req: Request, id):
    obj = db.query(type).get(id)
    


def set(type, db: Session, req: Request, dto: dtos.Base):
    obj = type(**dto.dict())
    db.merge(obj)
    db.commit()
    return obj


app = get_application()

class TypeName(str, Enum):
    Type = "types"
    Property = "properties"
    Component = "components"
    State = "states"

class ContentTypes(str, Enum):
    JSONSchema = "application/schema+json"
    SHACL = "application/shacl+json"
    JSONLD = "application/ld+json"
    HTML = "text/html"

TypeMap = {"properties":Property, "components":Component, "types":Type, "states":State}


class StdLink(str, Enum):
    Predecessor = "pred"
    Successor = "succ"
    Previous = "prev"
    Next = "next"





# TODO: replace with Enum classes: https://fastapi.tiangolo.com/sq/tutorial/path-params/#predefined-values
supported_links = {"properties":["pred", "succ", "prev", "next", "components", "states"], 
                   "components":["pred", "succ", "prev", "next", "properties", "states"], 
                   "states":["pred", "succ", "prev", "next", "properties", "components"]
                  
}



@app.get("/")
def get_type(req: Request, db: Session = Depends(get_db)):
    index = {}
    index["properties"] = db.query(Property).order_by(Property.id.desc()).all()
    index["components"] = db.query(Component).order_by(Component.id.desc()).all()
    index["types"] = db.query(Type).order_by(Type.id.desc()).all()
    index["states"] = db.query(State).order_by(State.id.desc()).all()
    return present(index, req.headers.get("accept"))


@app.get("/{source_type}")
def get_type(req: Request, source_type : TypeName, db: Session = Depends(get_db)):
    return TypeMap[source_type].current(db)
   

@app.get("/{source_type}/{id}")
def get_id(req: Request, source_type : TypeName, id : str,  accept: Union[ContentTypes, None] = None, db: Session = Depends(get_db)):
    item = TypeMap[source_type].get(db, id)
    if not item:
        raise HTTPException(status_code=404, detail="ID {id} of type {type} not found".format(type=source_type, id=id))
    return present(item, accept or req.headers.get("accept"))


@app.get("/{source_type}/{id}/{link_type}")
def get_id(req: Request, source_type : TypeName, id : str, link_type : StdLink, db: Session = Depends(get_db)):
    item = TypeMap[source_type].get(db, id)
    if not item:
        raise HTTPException(status_code=404, detail="ID {id} of type {type} not found".format(type=source_type, id=id))
    target = getattr(item, link_type)
    if target:
        return RedirectResponse(url="/{source_type}/{id}".format(source_type=source_type, id = target.id))
    else:
        raise HTTPException(status_code=404, detail="No object associated with {link_type} link".format(link_type = link_type))


@app.get("/{source_type}/{id}/related/{target_type}", summary="Get all objects of a given type related to the source object.")
def get_related(req: Request, source_type : TypeName, id : str, target_type : TypeName, db: Session = Depends(get_db)):
    item = TypeMap[source_type].get(db, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item with ID {id} not found.".format(id = id))
    if target_type == "properties":
        return item.related_properties
    elif target_type == "components":
        return item.related_components
    elif target_type == "types":
        return item.related_types
    elif target_type == "states":
        return item.related_states
    else:
        raise HTTPException(status_code=404, detail="Related type {type} not recognized.".format(type=type))


@app.get("/{source_type}/{id}/related/{target_type}/targets")
def get_related(req: Request, source_type : TypeName, id : str, target_type : TypeName, db: Session = Depends(get_db)):
    item = TypeMap[source_type].get(db, id)
    if not item:
        raise HTTPException(status_code=404, detail="Item with ID {id} not found.".format(id = id))
    
    if source_type == "components" and target_type == "properties":
        return db.query(Property).join(HasPropertyRelation).filter(HasPropertyRelation.source_id == item.id).all()
    elif source_type == "properties" and target_type == "components":
        return db.query(Component).join(HasPropertyRelation).filter(HasPropertyRelation.target_id == item.id).all()
    
    if source_type == "types" and target_type == "components":
        return db.query(Type).join(HasComponentRelation).filter(HasComponentRelation.source_id == item.id).all()
    elif source_type == "components" and target_type == "types":
        return db.query(Component).join(HasComponentRelation).filter(HasPropertyRelation.target_id == item.id).all()

    elif source_type == "states" and target_type == "components":
        return db.query(Component).join(StateComponentRelation).filter(StateComponentRelation.source_id == item.id).all()
    elif source_type == "components" and target_type == "states":
        return db.query(State).join(StateComponentRelation).filter(StateComponentRelation.target_id == item.id).all()
    
    elif source_type == "states" and target_type == "properties":
        return db.query(Property).join(StatePropertyRelation).filter(StatePropertyRelation.source_id == item.id).all()
    elif source_type == "properties" and target_type == "states":
         return db.query(State).join(StatePropertyRelation).filter(StatePropertyRelation.target_id == item.id).all()
    
    elif source_type == "states" and target_type == "types":
        return db.query(Type).join(StateTypeRelation).filter(StateTypeRelation.source_id == item.id).all()
    elif source_type == "types" and target_type == "states":
         return db.query(State).join(StatePropertyRelation).filter(StatePropertyRelation.target_id == item.id).all()

    else:
        raise HTTPException(status_code=404, detail="Related type {type} not recognized.".format(type=type))

@app.get("/{source_type}/{id}/related/{target_type}/{target_id}")
def get_related_instance(req: Request, source_type : TypeName, id : str, target_type : TypeName,  target_id : str, db: Session = Depends(get_db)):
    if source_type == "components" and target_type == "properties":
        return HasPropertyRelation.get(db, id, target_id)
    elif source_type == "properties" and target_type == "components":
        return HasPropertyRelation.get(db, target_id, id)

    elif source_type == "types" and target_type == "components":
        return HasComponentRelation.get(db, id, target_id)
    elif source_type == "types" and target_type == "components":
        return HasComponentRelation.get(db, target_id, id)

    elif source_type == "states" and target_type == "components":
        return StateComponentRelation.get(db, id, target_id)
    elif source_type == "components" and target_type == "states":
        return StateComponentRelation.get(db, target_id, id)

    elif source_type == "states" and target_type == "properties":
        return StatePropertyRelation.get(db, id, target_id)
    elif source_type == "properties" and target_type == "states":
        return StatePropertyRelation.get(db, target_id, id)

    elif source_type == "states" and target_type == "types":
        return StateTypeRelation.get(db, id, target_id)
    elif source_type == "types" and target_type == "states":
        return StateTypeRelation.get(db, target_id, id)

    else:
        raise HTTPException(status_code=404, detail="Unknown relation type from {source_type} to {target_type}".format(source_type=source_type, target_type = target_type))

from init import init_bsdd, init
@app.on_event("startup")
def startup():
    db = next(get_db())
    init_bsdd(db)
    init(db)
# /{source_type}/{source_id}/{rel}/{target_id}

# GET /{source_type}
# Get a Page of all current {source_type} instances

# POST /{source_type}
# Create a new instance of {source_type}

# PUT /{source_type}

# GET /{source_type}