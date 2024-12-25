from datetime import date
from pydantic import BaseModel,validator
from enum import Enum
from pydantic import BaseModel
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
  
class Album(BaseModel): 
    title:str
    release_date:date

  
class BandBase(BaseModel):
    name:str
    genre:GenreChoises
    albums:list[Album]=[]
    
class BandCreate(BandBase):
    @validator('genre',pre=True)
    def title_case_genre(cls,value):
        return value.title()
class BandWithID(BandBase):
    id:int
    