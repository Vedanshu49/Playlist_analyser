from pydantic import BaseModel, constr, validator
import re

class PlaylistID(BaseModel):
    playlist_id: constr(min_length=22, max_length=22)
    
    @validator('playlist_id')
    def validate_playlist_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9]{22}$', v):
            raise ValueError('Invalid Spotify playlist ID format')
        return v

class ErrorResponse(BaseModel):
    detail: str
    path: str = None
    timestamp: str = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str = None
    scope: str = None
