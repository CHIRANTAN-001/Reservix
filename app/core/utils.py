from fastapi import  Request
import jwt
from app.core.config import settings
from app.core.response import UnauthorizedError

from pydantic import BaseModel

def get_current_user(request: Request) -> str:
    """
    Extract the current user from the request.
    
    This function extracts the user from the Authorization header
    and validates the token. If the token is invalid or expired,
    it raises an UnauthorizedError.
    
    :param request: The request to extract the user from
    :return: The current user
    """
    token = request.headers.get("Authorization")
    
    if not token:
        raise UnauthorizedError("Token not found")
    
    try:
        # remove Bearer from the token
        token = token.split(" ")[1]
        # decode the token
        user = jwt.decode(
            jwt=token,
            algorithms=[settings.HASHING_ALG],
            key=settings.SECRET_KEY,
        )
        
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token has expired")
    
    except jwt.InvalidTokenError:
        raise UnauthorizedError("Invalid token")
    
    request.state.user = user
    return user["sub"]


def _build_update_clause(
    model: BaseModel,
) -> tuple[str, dict]:
    field_values = model.model_dump(exclude_unset=True)
    
    if not field_values:
        raise ValueError("No fields to update")
    
    # set_clause: "field1 = :field1, field2 = :field2"
    set_caluse = ", ".join(
        f"{field} = :{field}" for field in field_values
    )
    set_caluse = set_caluse + ", updated_at = NOW()"
    # bind_params: {"field1": value1, "field2": value2}
    bind_params = field_values.copy()
    
    return set_caluse, bind_params

def _build_insert_clause(
    model: BaseModel,
) -> tuple[str, dict]:
    field_values = model.model_dump(exclude_unset=False)
    
    if not field_values:
        raise ValueError("No fields to update")
    
    column_list = ", ".join(field_values.keys())
    placeholder_list = ", ".join(
        f":{field}" for field in field_values
    )
    
    insert_clause = f"({column_list}) VALUES ({placeholder_list})"
    
    bind_params = field_values.copy()
    
    return insert_clause, bind_params
