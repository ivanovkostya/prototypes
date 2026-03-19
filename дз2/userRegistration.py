from pydantic import BaseModel, Field, EmailStr, field_validator, ValidationError, model_validator
from datetime import datetime
import re

# Задание 1
class UserRegistration(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, pattern=r'^[a-zA-Z0-9_]+$')
    email: EmailStr
    password: str = Field(..., min_length=8)
    password_confirm: str
    age: int = Field(..., ge=18, le=120)
    registration_date: datetime = Field(default_factory=datetime.now)

    # Проверка пароля
    @field_validator('password')
    def validate_password(cls, v):
        if not any(c.isdigit() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        if not any(c.isupper() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну заглавную букву')
        if not any(c.islower() for c in v):
            raise ValueError('Пароль должен содержать хотя бы одну строчную букву')
        return v

    # Проверка совпадения паролей (лучше через model_validator)
    @model_validator(mode='after')
    def check_passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError('Пароли не совпадают')
        return self

    # Убираем password_confirm при сериализации
    def model_dump(self, *args, **kwargs):
        kwargs.setdefault('exclude', {'password_confirm'})
        return super().model_dump(*args, **kwargs)


# Функция регистрации
def register_user(data: dict):
    try:
        user = UserRegistration(**data)
        return {
            "success": True,
            "user": user.model_dump()
        }
    except ValidationError as e:
        return {
            "success": False,
            "errors": e.errors()
        }


# Задание 2
class UserRegistrationExtended(UserRegistration):
    full_name: str = Field(..., min_length=2)
    phone: str

    @field_validator('full_name')
    def validate_full_name(cls, v):
        if not v[0].isupper():
            raise ValueError('Имя должно начинаться с заглавной буквы')
        return v

    @field_validator('phone')
    def validate_phone(cls, v):
        pattern = r'^\+\d-\d{3}-\d{2}-\d{2}$'
        if not re.match(pattern, v):
            raise ValueError('Телефон должен быть в формате +X-XXX-XX-XX')
        return v



data = {
    "username": "john_doe",
    "email": "john@example.com",
    "password": "Password123",
    "password_confirm": "Password123",
    "age": 25,
    "full_name": "John",
    "phone": "+7-999-12-34"
}

user = UserRegistrationExtended(**data)
print(user.model_dump())
