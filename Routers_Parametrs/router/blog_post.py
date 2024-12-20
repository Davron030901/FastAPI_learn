from fastapi import APIRouter,Query,Path,Body
from typing import Optional,List,Dict
from pydantic import BaseModel

router=APIRouter(
    prefix='/blog',
    tags=['blog'],
)
class Image(BaseModel):
    url:str
    alias:str
class BlogModel(BaseModel):
    title:str
    content:str
    nb_comments:int 
    published:Optional[bool]
    tags:List[str]=[]
    metadata:Dict[str,str]={'Key':'Value'}
    image:Optional[Image]=None

@router.post('/new')
def create_blog(blog:BlogModel):
    return {"data":blog}

@router.post('/new/{id}')
def create_blogs(blog:BlogModel,id:int,version:int=1):
    return {
        'id':id,
        "data":blog,
        'version':version}
    
@router.post('/new/{id}/comment/{comment_id}')    
def create_comment(
    blog: BlogModel,
    id: int,
    comment_title: int = Query(
        None,
        title="Comment Object",
        description="Some description for comment_title",
        alias="commentTitle",
        deprecated=True,
    ),
    content: str = Body(
        ...,
        min_length=10,
        max_length=100,
        regex="^[a-z\s]*$",
    ),
    v: Optional[List[str]] = Query(["1.0", "2.0"]),
    comment_id: int = Path(..., gt=5, le=10) 
):
    return {
        "blog": blog,
        "id": id,
        "comment_id": comment_id,
        "comment_title": comment_title,
        "content": content,
        "version": v,
    }
