# SPDX-FileCopyrightText: © 2023 Devon D. Sparks <devonsparks.com>
# SPDX-License-Identifier: MIT

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import AnyUrl
from sqlalchemy.orm import Session
from models import Property, Component, Type, PropertyComponentAssignment, ComponentTypeAssignment
from presenters import present
from database import Base, engine, get_db
import dtos


def mime_types():
    return {
        200: {
            'content': {
                'application/json': {},
                'application/shacl+json': {},
                'application/ld+json': {},
                'application/schema+json': {}
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
    if not obj:
        return HTTPException(status_code=404)
    return present(obj, req.headers.get("content-type"))


def set(type, db: Session, req: Request, dto: dtos.Base):
    obj = type(**dto.dict())
    db.merge(obj)
    db.commit()
    return obj


app = get_application()


@app.get("/properties", responses=mime_types())
def get_property_definition(req: Request, id: AnyUrl, db: Session = Depends(get_db)):
    return get(Property, db, req, id)


@app.put("/properties")
def put_property_definition(req: Request, dto: dtos.Property, db: Session = Depends(get_db)):
    return set(Property, db, req, dto)


@app.get("/components", responses=mime_types())
def get_component_definition(req: Request, id: AnyUrl, db: Session = Depends(get_db)):
    return get(Component, db, req, id)


@app.put("/components")
def put_component_definition(req: Request, dto: dtos.Component, db: Session = Depends(get_db)):
    return set(Component, db, req, dto)


@app.get("/components/assignments", responses=mime_types())
def get_component_assignment(req: Request, component_id: AnyUrl, property_id: AnyUrl, db: Session = Depends(get_db)):
    return db.query(PropertyComponentAssignment).filter(PropertyComponentAssignment.component_id == component_id,
                                                        PropertyComponentAssignment.property_id == property_id)


@app.put("/components/assignments")
def put_component_assignment(req: Request, dto: dtos.PropertyComponentAssignment, db: Session = Depends(get_db)):
    return set(PropertyComponentAssignment, db, req, dto)


@app.get("/types", responses=mime_types())
def get_type_definition(req: Request, id: AnyUrl, db: Session = Depends(get_db)):
    return get(Type, db, req, id)


@app.put("/types")
def put_type_definition(req: Request, dto: dtos.Component, db: Session = Depends(get_db)):
    return set(Type, db, req, dto)


@app.get("/types/assignments", responses=mime_types())
def get_type_assignment(req: Request, type_id: AnyUrl, component_id: AnyUrl, db: Session = Depends(get_db)):
    return db.query(ComponentTypeAssignment).filter(ComponentTypeAssignment.component_id == component_id,
                                                    ComponentTypeAssignment.type_id == type_id)


@app.put("/components/assignments")
def put_type_assignment(req: Request, dto: dtos.ComponentTypeAssignment, db: Session = Depends(get_db)):
    return set(ComponentTypeAssignment, db, req, dto)

"""
@app.on_event("startup")
def startup():
    from init import init
    init(next(get_db()))
"""