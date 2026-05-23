from datetime import datetime
from pydantic import BaseModel, field_validator
from typing import Optional
import re


class SendOTPIn(BaseModel):
    phone_number: str

    @field_validator("phone_number")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^09[0-9]{9}$", v):
            raise ValueError("شماره موبایل معتبر نیست")
        return v


class VerifyOTPIn(BaseModel):
    phone_number: str
    code: str
    password: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) < 6:
            raise ValueError("رمز عبور باید حداقل ۶ کاراکتر باشد")
        return v


class LoginIn(BaseModel):
    phone_number: str
    password: str


class ForgotPasswordIn(BaseModel):
    phone_number: str


class ResetPasswordIn(BaseModel):
    phone_number: str
    code: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("رمز عبور جدید باید حداقل ۶ کاراکتر باشد")
        return v


class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("رمز عبور جدید باید حداقل ۶ کاراکتر باشد")
        return v


class TokenOut(BaseModel):
    access: str
    refresh: str


class AddressIn(BaseModel):
    title:       str  = ""
    province:    str
    city:        str
    street:      str
    postal_code: str
    is_default:  bool = False


class AddressOut(BaseModel):
    id:          int
    title:       str
    province:    str
    city:        str
    street:      str
    postal_code: str
    is_default:  bool

    model_config = {"from_attributes": True}


class ProfileOut(BaseModel):
    id:          int
    phone_number: str
    full_name:   str
    email:       Optional[str] = None
    national_id: Optional[str] = None
    date_joined: datetime

    model_config = {"from_attributes": True}


class UpdateProfileIn(BaseModel):
    full_name:   Optional[str] = None
    email:       Optional[str] = None
    national_id: Optional[str] = None
