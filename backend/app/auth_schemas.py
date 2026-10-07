from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


UserRole = Literal["CITIZEN", "INVESTIGATOR"]


class RegistrationRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name")
    @classmethod
    def name_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("name must not be blank")

        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class PublicUser(BaseModel):
    user_id: str
    name: str
    email: EmailStr
    role: UserRole


class AuthenticationResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    user: PublicUser