# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.logger import logger
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import AnyUrl
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.orm import Session
from models import Property, Component, State, Item

from database import Base, engine, get_db
import dtos

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
type_map = {"properties":Property, "components":Component, "states":State}

# TODO: replace with Enum classes: https://fastapi.tiangolo.com/sq/tutorial/path-params/#predefined-values
supported_links = {"properties":["pred", "succ", "prev", "next", "components", "states"], 
                   "components":["pred", "succ", "prev", "next", "properties", "states"], 
                   "states":["pred", "succ", "prev", "next", "properties", "components"]
                  
}
def check_type(db, type):
    if type not in type_map:
        raise HTTPException(status_code=404, detail="Type '{type}' not supported.".format(type=type))

def check_id(db, type, id):
    check_type(db, type)
    if not db.get(type_map[type], id):
        raise HTTPException(status_code=404, detail="No ID '{id}' found in '{type}' dictionary.".format(type=type, id=id))

def check_link(db, type, id, link):
    check_id(db, type, id)
    if link not in supported_links[type]:
        raise HTTPException(status_code=404, detail="Link '{link}' not supported on '{type}'".format(link=link, type=type))

@app.get("/")
def get_type(req: Request, db: Session = Depends(get_db)):
    index = {}
    index["properties"] = db.query(Property).order_by(Property.id.desc()).all()
    index["components"] = db.query(Component).order_by(Component.id.desc()).all()
    index["states"] = db.query(State).order_by(State.id.desc()).all()
    return present(index, req.headers.get("accept"))


@app.get("/{type}")
def get_type(req: Request, type : str,  db: Session = Depends(get_db)):
    check_type(db, type)
    top = type_map[type].top(db)
    return RedirectResponse("/{type}/{id}".format(type=type,id=top.id))


@app.get("/{type}/{id}")
def get_id(req: Request, type : str, id : int, db: Session = Depends(get_db)):
    item = type_map[type].get(db, id)
    if not item:
        raise HTTPException(status_code=404, detail="ID {id} of type {type} not found".format(type=type, id=id))
    return present(item, req.headers.get("accept"))


@app.get("/{type}/{id}/{link}")
def getter_link(req: Request, type : str, id : int, link : str,  db: Session = Depends(get_db)):
    check_link(db, type, id, link)
    next = getattr(type_map[type].get(db, id), link)
    if next == None:
        raise HTTPException(status_code=404, detail="No link '{link}' available on {type} ID '{id}'".format(link=link, type=type, id=id))
    elif isinstance(next, InstrumentedList):
        return next
    else:
        return RedirectResponse("/{type}/{id}".format(type=type,id=next.id))
        

@app.on_event("startup")
def startup():
    from init import init
    init(next(get_db()))
