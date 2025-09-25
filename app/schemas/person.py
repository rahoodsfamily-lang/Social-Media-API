from pydantic import BaseModel

class PersonCreate(BaseModel):
    name: str
    age: int

class PersonResponse(BaseModel):
    element_id_property: str 
    name: str
    age: int
