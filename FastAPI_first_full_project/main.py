from fastapi import FastAPI,HTTPException,Query,Path,Depends
# from contextlib import asynccontextmanager
from typing import Annotated
from sqlmodel import Session,select
from models import *
from db import init_db,get_session


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     init_db()
#     yield 


# app=FastAPI(lifespan=lifespan)
app=FastAPI()

BANDS=[
    {'id':1,'name':'The Beatles','genre':'Rock'},
    {'id':2,'name':'The Rolling Stones','genre':'Electronik'},
    {'id':3,'name':'Led Zeppelin','genre':'Metal','albums':[
        {'title':'Led Zeppelin IV','release_date':"1971-07-21"},
        {'title':'Led Zeppelin II','release_date':"1969-11-29"},
        {'title':'Led Zeppelin III','release_date':"1973-01-01"},
    ]},
    {'id':4,'name':'Pink Floyd','genre':'Hip-Hop'},
]

@app.get("/bands")
async def get_bands(
    genre:Genre | None=None,
    q:Annotated[str | None, Query(max_length=10)] = None,
    session:Session=Depends(get_session)
    )-> list[Band]:
    band_list=session.exec(select(Band)).all()
    if genre:
        band_list=[
        b for b in band_list if b.genre.value.lower()==genre.value
     ]
    if q:
        band_list=[
            b for b in band_list if q.lower() in b.name.lower()
        ]   
    return band_list

@app.get("/bands/{band_id}")
async def band(band_id:Annotated[int,Path(title="Band ID")],
               session:Session=Depends(get_session))-> Band:

    band= session.get(Band,band_id)
    
    if band is None:
        raise HTTPException(status_code=404,detail="Band not found")
    return band

@app.post("/bands")
async def create_band(
    band_data:BandCreate,
    session:Session=Depends(get_session)) -> Band:
    band=Band(name=band_data.name,genre=band_data.genre)
    session.add(band)
    
    if band_data.albums:
        for album_data in band_data.albums:
            album=Album(title=album_data.title,release_date=album_data.release_date,band=band)
            session.add(album)
    
    session.commit()
    session.refresh(band)
    return band

