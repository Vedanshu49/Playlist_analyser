from fastapi import FastAPI, HTTPException, Request, Depends, Path, Query
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi_csrf_protect import CsrfProtect
from fastapi_csrf_protect.exceptions import CsrfProtectError
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
import uuid
import logging
from typing import Optional
from datetime import datetime
from api.health import HealthCheck
from api.middleware import CacheControlMiddleware, ResponseTimeMiddleware
from api.schemas import PlaylistID, ErrorResponse

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
SPOTIPY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
SECRET_KEY = os.getenv("SECRET_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL")
PRODUCTION_URL = os.getenv("PRODUCTION_URL")
API_VERSION = "1.0.0"

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set")

app = FastAPI(title="Playlist Analyser API", version="1.0.0")

# Rate limiting configuration
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

@app.exception_handler(CsrfProtectError)
def csrf_protect_exception_handler(request: Request, exc: CsrfProtectError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

class CsrfSettings(BaseModel):
    secret_key:str = SECRET_KEY

@CsrfProtect.load_config
def get_csrf_config():
    return CsrfSettings()

# CORS configuration
origins = os.getenv("CORS_ORIGINS", "").split(",")
if not origins:
    raise RuntimeError("CORS_ORIGINS environment variable is not set")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Restrict to only needed methods
    allow_headers=["Content-Type", "Set-Cookie", "X-CSRF-Token"],
)

# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; connect-src 'self' https://api.spotify.com;"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# Error handling middleware
class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.exception("Unhandled exception occurred")
            
            # Sanitize error response in production
            if os.getenv("ENVIRONMENT") == "production":
                error_detail = "An internal server error occurred"
            else:
                error_detail = str(e)
            
            return JSONResponse(
                status_code=500,
                content={"detail": error_detail}
            )

app.add_middleware(ErrorHandlerMiddleware)

# Add caching and response time middleware
from middleware import CacheControlMiddleware, ResponseTimeMiddleware
app.add_middleware(CacheControlMiddleware, cache_time=3600)  # 1 hour cache
app.add_middleware(ResponseTimeMiddleware)

# Define the scopes for the Spotify API
SCOPE = "user-top-read playlist-read-private"

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SCOPE
    )

def refresh_token_if_expired(request: Request) -> Optional[dict]:
    """Helper function to refresh the Spotify token if expired"""
    token_info = request.session.get('token_info')
    token_expiry = request.session.get('token_expiry')
    
    if not token_info or not token_expiry:
        return None
        
    now = datetime.now().timestamp()
    is_expired = float(token_expiry) - now < 60  # Check if token expires in less than 60 seconds
    
    if is_expired:
        try:
            sp_oauth = create_spotify_oauth()
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            request.session['token_info'] = token_info
            request.session['token_expiry'] = str(datetime.now().timestamp() + token_info['expires_in'])
            return token_info
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None
            
    return token_info

# Health check endpoint
@app.get("/health")
async def health_check(request: Request):
    status = HealthCheck.get_status()
    
    # Check Spotify API connection if we have credentials
    if SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET:
        auth_manager = spotipy.oauth2.SpotifyClientCredentials(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET
        )
        sp = spotipy.Spotify(auth_manager=auth_manager)
        status["spotify_api"] = HealthCheck.check_spotify_connection(sp)
    
    return status

# Version endpoint
@app.get("/api/version")
async def get_version():
    return {"version": API_VERSION}

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    logger.warning(f"404 Not Found: {request.url}")
    return JSONResponse(
        status_code=404,
        content={
            "detail": "The requested resource was not found",
            "path": str(request.url)
        }
    )

@app.get("/")
def read_root(request: Request):
    return {"message": "Welcome to the Playlist Analyser API"}

@app.get("/api/login")
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return RedirectResponse(auth_url)

@app.get("/api/callback")
async def callback(request: Request):
    sp_oauth = create_spotify_oauth()
    error = request.query_params.get('error')
    code = request.query_params.get('code')
    
    if error:
        logger.error(f"Spotify OAuth error: {error}")
        return RedirectResponse(url=f"{FRONTEND_URL}/error?message=Authentication failed")
        
    if not code:
        logger.error("No code parameter received")
        return RedirectResponse(url=f"{FRONTEND_URL}/error?message=Invalid callback")

    try:
        token_info = sp_oauth.get_access_token(code)
        if not token_info:
            raise ValueError("Failed to get access token")
            
        # Store token info in session with expiration
        request.session['token_info'] = token_info
        request.session['token_expiry'] = str(datetime.now().timestamp() + token_info['expires_in'])
        
        # Set secure session cookie
        response = RedirectResponse(url=PRODUCTION_URL)
        response.set_cookie(
            'session',
            request.session['session'],
            httponly=True,
            secure=True,
            samesite='lax'
        )
        return response
        
    except Exception as e:
        logger.exception("Error during callback processing")
        return RedirectResponse(url=f"{FRONTEND_URL}/error?message=Authentication error")

@app.get("/api/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url='http://localhost:3000')

@app.get("/api/me")
def get_me(request: Request):
    token_info = request.session.get('token_info', None)
    if not token_info:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sp = spotipy.Spotify(auth=token_info['access_token'])
    try:
        user = sp.current_user()
        return user
    except SpotifyException as e:
        raise HTTPException(status_code=e.http_status, detail=e.msg)

@app.get("/api/me/top-artists")
def get_top_artists(request: Request):
    token_info = request.session.get('token_info', None)
    if not token_info:
        raise HTTPException(status_code=401, detail="Not authenticated")

    sp = spotipy.Spotify(auth=token_info['access_token'])
    try:
        top_artists = sp.current_user_top_artists(limit=10, time_range='medium_term')
        return top_artists
    except SpotifyException as e:
        raise HTTPException(status_code=e.http_status, detail=e.msg)


from schemas import PlaylistID, ErrorResponse
from datetime import datetime

@app.get("/api/playlist/{playlist_id}")
async def get_playlist(request: Request, playlist_id: str = Path(..., description="Spotify playlist ID")):
    # Validate playlist ID
    try:
        PlaylistID(playlist_id=playlist_id)
    except ValueError as e:
        logger.warning(f"Invalid playlist ID format: {playlist_id}")
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                detail="Invalid playlist ID format",
                path=str(request.url),
                timestamp=datetime.now().isoformat()
            ).dict()
        )
    
    # Get token and refresh if needed
    token_info = refresh_token_if_expired(request) if request.session.get('token_info') else None
    
    try:
        if token_info:
            sp = spotipy.Spotify(auth=token_info['access_token'])
        else:
            # Fallback to client credentials flow if user is not logged in
            auth_manager = spotipy.oauth2.SpotifyClientCredentials(
                client_id=SPOTIPY_CLIENT_ID,
                client_secret=SPOTIPY_CLIENT_SECRET
            )
            sp = spotipy.Spotify(auth_manager=auth_manager)

        playlist = sp.playlist(playlist_id)
        
        # Validate response data
        if not playlist or not isinstance(playlist, dict):
            raise ValueError("Invalid response from Spotify API")
            
        return {
            "name": playlist.get("name"),
            "owner": {
                "display_name": playlist.get("owner", {}).get("display_name"),
                "id": playlist.get("owner", {}).get("id")
            },
            "followers": {
                "total": playlist.get("followers", {}).get("total", 0)
            },
            "images": [{"url": img.get("url")} for img in playlist.get("images", [])[:1]] if playlist.get("images") else []
        }
    except SpotifyException as e:
        logger.error(f"Spotify API error: {e.msg}")
        raise HTTPException(
            status_code=e.http_status,
            detail={"message": e.msg, "code": e.code}
        )
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error in get_playlist")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/playlist/{playlist_id}/tracks")
@limiter.limit("30/minute")  # Rate limit for track analysis
async def get_playlist_tracks(
    request: Request,
    playlist_id: str = Path(..., description="Spotify playlist ID"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=100, description="Number of tracks per page")
):
    # Validate playlist ID
    try:
        PlaylistID(playlist_id=playlist_id)
    except ValueError as e:
        logger.warning(f"Invalid playlist ID format: {playlist_id}")
        return JSONResponse(
            status_code=400,
            content=ErrorResponse(
                detail="Invalid playlist ID format",
                path=str(request.url),
                timestamp=datetime.now().isoformat()
            ).dict()
        )

    # Get token and refresh if needed
    token_info = refresh_token_if_expired(request) if request.session.get('token_info') else None
    
    try:
        if token_info:
            sp = spotipy.Spotify(auth=token_info['access_token'])
        else:
            auth_manager = spotipy.oauth2.SpotifyClientCredentials(
                client_id=SPOTIPY_CLIENT_ID,
                client_secret=SPOTIPY_CLIENT_SECRET
            )
            sp = spotipy.Spotify(auth_manager=auth_manager)
        
        # Get tracks with pagination
        results = sp.playlist_tracks(
            playlist_id,
            offset=offset,
            limit=limit,
            fields='items(track(id,name,artists(name),preview_url)),total,next'
        )
        
        if not isinstance(results, dict):
            raise ValueError("Invalid response from Spotify API")
            
        tracks = results.get('items', [])
        total_tracks = results.get('total', 0)
        
        # Extract valid track IDs
        track_ids = [
            track.get('track', {}).get('id')
            for track in tracks
            if track.get('track') and track.get('track', {}).get('id')
        ]
        
        if not track_ids:
            return {
                "tracks": [],
                "total": total_tracks,
                "offset": offset,
                "limit": limit
            }
            
        # Get audio features in batches
        audio_features = []
        batch_size = 100
        for i in range(0, len(track_ids), batch_size):
            batch = track_ids[i:i + batch_size]
            features = sp.audio_features(batch)
            if features:
                audio_features.extend([f for f in features if f])
                
        audio_features_map = {af['id']: af for af in audio_features if af}
        
        # Process track data
        track_data = []
        for track in tracks:
            track_info = track.get('track')
            if not track_info or not track_info.get('id'):
                continue
                
            af = audio_features_map.get(track_info['id'])
            if not af:
                continue
                
            track_data.append({
                "id": track_info['id'],
                "name": track_info.get('name', ''),
                "artists": [artist.get('name', '') for artist in track_info.get('artists', [])],
                "preview_url": track_info.get('preview_url'),
                "danceability": af.get('danceability', 0),
                "energy": af.get('energy', 0),
                "valence": af.get('valence', 0),
                "tempo": af.get('tempo', 0)
            })
            
        return {
            "tracks": track_data,
            "total": total_tracks,
            "offset": offset,
            "limit": limit
        }
        
    except SpotifyException as e:
        logger.error(f"Spotify API error: {e.msg}")
        raise HTTPException(
            status_code=e.http_status,
            detail={"message": e.msg, "code": e.code}
        )
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error in get_playlist_tracks")
        raise HTTPException(status_code=500, detail="Internal server error")