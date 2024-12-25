from datetime import date
from pydantic import validator
from enum import Enum
from sqlmodel import Field,SQLModel,Relationship
class Genre(Enum):
    ROCK='rock'
    ELECTRONIK='electronic'
    METAL='metal'
    HIP_HOP='hip-hop'
class GenreChoises(Enum):
    ROCK='Rock'
    ELECTRONIK='Electronic'
    METAL='Metal'
    HIP_HOP='Hip-Hop'
  
class AlbumBase(SQLModel): 
    title:str
    release_date:date
    band_id:int | None=Field(foreign_key='band.id')
class Album(AlbumBase,table=True):
    id:int=Field(primary_key=True)
    band:"Band"=Relationship(back_populates='albums')
class BandBase(SQLModel):
    name: str
    genre: GenreChoises

    # Remove albums from BandBase since it's causing the issue

class BandCreate(BandBase):
    albums:list[AlbumBase] | None=None
    @validator('genre',pre=True)
    def title_case_genre(cls,value):
        return value.title()
    
class Band(BandBase, table=True):
    id: int = Field(primary_key=True)
    albums: list[Album] = Relationship(back_populates='band')
    date_formed:date
    
# pip install sqlmodel 