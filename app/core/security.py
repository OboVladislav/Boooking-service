from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

# def hash_password(password: str) -> str:
#     password = password[:72]
#     return pwd_context.hash(password)
#
# def verify_password(password: str, hashed_password: str) -> bool:
#     return pwd_context.verify(password, hashed_password)


def hash_password(password: str) -> str:
    bpassword = password.encode("utf-8")[:72]  # безопасная обрезка
    return pwd_context.hash(bpassword)

def verify_password(password: str, hashed_password: str) -> bool:
    bpassword = password.encode("utf-8")[:72]
    return pwd_context.verify(bpassword, hashed_password)