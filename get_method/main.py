from fastapi import FastAPI
from enum import Enum
from typing import Optional

myApp=FastAPI()



@myApp.get('/hello')
def  index():
    return 'Hello World'


@myApp.get('/hi')
def  ind():
    return {"massage":"Hi"}

# @myApp.get('/blog/all')
# def get_all():
#     return {'massage':'All blogs'}

# @myApp.get('/blog/all')
# def get_all_blogs(page,page_size):
#     return {'massage': f'All {page_size} blogs on page {page}'}

# @myApp.get('/blog/all')
# def get_all_blogs(page:int=1,page_size:int=10):
#     return {'massage': f'All {page_size} blogs on page {page}'}

@myApp.get('/blog/all')
def get_all_blogs(page:int=1,page_size:Optional[int]=None):
    return {'massage': f'All {page_size} blogs on page {page}'}

@myApp.get('/blog/{id}/comments/{comment_id}')
def get_comment(id:int,comment_id:int,valid:bool=True,username:Optional[str]=None):
    return {'massage':f'Blog_id {id} , comment_id {comment_id}, validate {valid},username {username}'}

class BlogType(str,Enum):
    short='short'
    story='story'
    howto='howto'
    
@myApp.get('/blog/{id}')
def get_method(id:int):
    return {'massage':f'Blog id={id}'}

@myApp.get('/blog/type/{type}')
def blog_type(type:BlogType):
    return {'massage':f'Blog type {type}'}