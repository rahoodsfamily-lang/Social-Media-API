from fastapi import HTTPException
from app.models.person import Person
from app.schemas.person import PersonCreate

def create_person(data: PersonCreate):
    if Person.nodes.get_or_none(name=data.name):
        raise HTTPException(status_code=400, detail="Person already exists")
    new_person = Person(name=data.name, age=data.age).save()
    return new_person

def get_person(name: str):
    person = Person.nodes.get_or_none(name=name)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    return person

def list_persons():
    return Person.nodes.all()

def update_person(name: str, data: PersonCreate):
    person = Person.nodes.get_or_none(name=name)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    person.age = data.age
    person.save()
    return person

def delete_person(name: str):
    person = Person.nodes.get_or_none(name=name)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    person.delete()
    return {"message": f"Person '{name}' deleted"}
