from fastapi import FastAPI,status,Response

app = FastAPI()

@app.get('/blog/all',tags=['blog'],summary='Retrive all blogs',description='This API call simulates fetching all blogs.',response_description='This list of available blogs')
def all_blogs():
    return {'message':'all blogs'}

@app.get('blog/{id}/comments/{comment_id}',tags=['blog','comments'])
def get_comment(id:int,comment_id:int,valid:bool=True,username:str=None):
    """
    Simulates retrieving a comment of a blog
    
    -**id**: The id of the blog
    
    -**comment_id**: The id of the comment
    
    -**valid**: Whether the comment is valid or not
    
    -**username**: The username
    """
    return {'message':f'blog id {id} comment id {comment_id}'}

@app.get("/blog/{id}",status_code=200)
def get_blog(id:int): 
    if id>5:
        return {'erroe':f'Blog {id} not found'}
    else:
        return {"massage":f'Blog with id {id}'}
    
@app.get("/blogs/{id}",status_code=status.HTTP_404_NOT_FOUND )
def get_blog(id:int): 
    if id>5:
        return {'erroe':f'Blog {id} not found'}
    else:
        return {"massage":f'Blog with id {id}'}
    
@app.get("/blogh/{id}",status_code=status.HTTP_200_OK )
def get_blog(id:int,response:Response): 
    if id>5:
        response.status_code=status.HTTP_404_NOT_FOUND
        return {'erroe':f'Blog {id} not found'}
    else:
        response.status_code=status.HTTP_200_OK
        return {"massage":f'Blog with id {id}'}