import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class LocationCreate(BaseModel):
    name: str
    admin_id: Optional[UUID] = None
    institution_actors_id: Optional[UUID] = None


class Location(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime.date
    last_modified: datetime.datetime
    prep_delete: Optional[datetime.datetime]
    admin: 'Person'


class LocationShow(Location):
    departments: list['Department']
    teams_of_actors: list['TeamOfActors']
    institution_actors: 'InstitutionActors'

    @field_validator('departments', 'teams_of_actors')
    def set_to_list(cls, values):  # sourcery skip: identity-comprehension
        return [v for v in values]


class InstitutionActorsCreate(BaseModel):
    name: str
    admin_id: Optional[UUID] = None


class InstitutionActors(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    created_at: datetime.date
    last_modified: datetime.datetime
    prep_delete: Optional[datetime.datetime]


class InstitutionActorsShow(InstitutionActors):
    actors: list['Actor']
    admin: 'Person'
    locations: list[Location]


class DepartmentCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    username: str
    password: str
    name: str
    descriptive_name: str
    location_id: UUID


class Department(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    password: str
    name: str
    descriptive_name: str
    created_at: datetime.date
    last_modified: datetime.datetime
    prep_delete: Optional[datetime.datetime]
    location: Location


class PersonCreate(BaseModel):
    id: Optional[UUID] = None
    username: str
    password: str
    f_name: str
    l_name: str
    location_of_admin_id: Optional[UUID] = None
    institution_actors_of_admin_id: Optional[UUID] = None


class Person(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    password: str
    f_name: str
    l_name: str
    created_at: datetime.date
    last_modified: datetime.datetime
    prep_delete: Optional[datetime.datetime]


class PersonShow(Person):
    location_of_admin: Optional[Location] = None
    institution_actors_of_admin: Optional['InstitutionActors'] = None


class ActorCreate(PersonCreate):
    institution_actors_id: Optional[UUID] = None
    artist_name: str


class Actor(Person):
    model_config = ConfigDict(from_attributes=True)

    artist_name: str
    team_of_actors: Optional['TeamOfActors']
    institution_actors: InstitutionActors


class ActorShow(Actor):
    location_of_admin: Optional[Location] = None
    institution_actors_of_admin: Optional['InstitutionActors'] = None


class TeamOfActorsCreate(BaseModel):
    id: Optional[UUID] = None
    location_id: UUID
    actor_ids: list[UUID]


class TeamOfActors(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    location: Location


class TeamOfActorsShow(TeamOfActors):
    actors: list[Actor]

    @field_validator('actors')
    def set_to_list(cls, values):  # sourcery skip: identity-comprehension
        return [v for v in values]


class SuperUserCreate(BaseModel):
    username: str
    password: str
    f_name: str
    l_name: str


class SuperUser(SuperUserCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    id: UUID | None = None
    authorizations: list[str]
