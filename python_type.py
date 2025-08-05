# 
def get_full_name(first_name:str,last_name:str):
    full_name=first_name.title()+" "+last_name.title()
    return full_name

print(get_full_name("john","doe"))

def get_name_with_age(name:str,age:int):
    name_with_age=name+ " is this old: " + str(age)
    return name_with_age

print(get_name_with_age("John", 30))

def get_items(item_a:str,item_b:int,item_c:float,item_d:bool,item_e:bytes):
    return item_a, item_b, item_c, item_d, item_e


print(get_items("apple", 5, 3.14, True, b'hello'))

def process_items(items:list[str]):
    for item in items:
        print(item)

items_list = ["apple", "banana", "cherry"]
process_items(items_list)

from typing import List

def process_items(items: List[str]):
    for item in items:
        print(item)
items_list = ["apple", "banana", "cherry"]
process_items(items_list)

def process_items(items_t:tuple[int,int,str], item_s:set[bytes]):
    return items_t, item_s

items_tuple = (1, 2, "three")
items_set = {b'one', b'two', b'three'}
print(process_items(items_tuple, items_set))

def process_items(prices: dict[str,float]):
    for item_name,item_price in prices.items():
        print(item_name)
        print(item_price)

prices_dict = {"apple": 1.2, "banana": 0.5, "cherry": 2.0}
process_items(prices_dict)

def process_items(item:int|str):
    print(item)
item1 = 42
item2 = "Hello"     
process_items(item1)
process_items(item2)

from typing import Optional

def say_hi(name:Optional[str]=None):
    if name is not None:
        print(f"Hey {name}!")
    else:
        print("Hello World!")

say_hi("Alice")
say_hi()

def say_hi(name:str | None=None):
    if name is not None:
        print(f"Hey {name}!")
    else:
        print("Hello World!")

say_hi("Alice")
say_hi()

from typing import Optional

def say_hi(name: Optional[str]):
    print(f"Hey {name}!")

say_hi("Alice")
say_hi(None)    

def say_hi(name: str | None ):
    print(f"Hey {name}!")

say_hi("Alice")
say_hi(None)

class Person:
    def __init__(self,name:str):
        self.name=name
def say_hi(person:Person):
    return one_person.name
one_person = Person("Alice")
print(say_hi(one_person))

from datetime import datetime
from pydantic import BaseModel

class User(BaseModel):
    id :int
    name: str
    signup_ts:datetime | None = None
    friends: list[int] = []

external_data={
    "id": "1",
    "name": "Alice",
    "signup_ts": datetime.now(),
    "friends": [2, 3]

}

user = User(**external_data)
print(user)
print(user.id)

from typing import Annotated
def say_hello(name: Annotated[str,"Name of the person to greet"])->str:
    return f"Hello, {name}!"

print(say_hello("Alice"))