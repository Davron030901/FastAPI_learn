from fastapi import APIRouter,status,Response
router=APIRouter(
    prefix='/blog',
    tags=['blog']
    )

@router.get('/')


@router.get('/all',summary='Retrive all blogs',description='This API call simulates fetching all blogs.',response_description='This list of available blogs')
def all_blogs():
    return {'message':'all blogs'}

@router.get('blog/{id}/comments/{comment_id}',tags=['comments'])
def get_comment(id:int,comment_id:int,valid:bool=True,username:str=None):
    """
    Simulates retrieving a comment of a blog
    
    -**id**: The id of the blog
    
    -**comment_id**: The id of the comment
    
    -**valid**: Whether the comment is valid or not
    
    -**username**: The username
    """
    return {'message':f'blog id {id} comment id {comment_id}'}


@router.get("/{id}",status_code=status.HTTP_200_OK )
def get_blog(id:int,response:Response): 
    if id>5:
        response.status_code=status.HTTP_404_NOT_FOUND
        return {'erroe':f'Blog {id} not found'}
    else:
        response.status_code=status.HTTP_200_OK
        return {"massage":f'Blog with id {id}'}