from fastapi import FastAPI,HTTPException,Query,Path
from typing import Annotated
from schemas import *
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
    genre:Genre|None=None,
    q:Annotated[str | None, Query(max_length=10)] = None,
    )-> list[BandWithID]:
    band_list=[BandWithID(**b) for b in BANDS ]
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
async def band(band_id:Annotated[int,Path(title="Band ID")])-> BandWithID:
    band=next((BandWithID(**b) for b in BANDS if b['id']==band_id),None)
    if band is None:
        raise HTTPException(status_code=404,detail="Band not found")
    return band

@app.get("/bands/genre/{genre}",status_code=206)
async def bands(genre:Genre)-> list[dict]:
    return [
        b for b in BANDS if b['genre'].lower()==genre.value
    ]

@app.post("/bands")
async def create_band(band_data:BandCreate) -> BandWithID:
    id=BANDS[-1]['id']+1
    band=BandWithID(id=id,**band_data.model_dump()).model_dump()
    BANDS.append(band)
    return band