from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
import uuid

load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

app = FastAPI()

# This should be a secret key for session management
SECRET_KEY = os.urandom(24).hex()

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# CORS (Cross-Origin Resource Sharing) middleware
origins = [
    "http://localhost:3000",  # React app
    "https://playlist-analyser.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define the scopes for the Spotify API
SCOPE = "user-top-read playlist-read-private"

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=SCOPE
    )

@app.get("/")
def read_root(request: Request):
    return {"message": "Welcome to the Playlist Analyser API"}

@app.get("/login")
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return RedirectResponse(auth_url)

@app.get("/callback")
def callback(request: Request):
    sp_oauth = create_spotify_oauth()
    code = request.query_params.get('code')
    token_info = sp_oauth.get_access_token(code)
    request.session['token_info'] = token_info
    return RedirectResponse(url='https://playlist-analyser.vercel.app') # Redirect to frontend

@app.get("/logout")
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


@app.get("/api/playlist/{playlist_id}")
def get_playlist(playlist_id: str, request: Request):
    token_info = request.session.get('token_info', None)
    
    if token_info:
        sp = spotipy.Spotify(auth=token_info['access_token'])
    else:
        # Fallback to client credentials flow if user is not logged in
        auth_manager = spotipy.oauth2.SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
        sp = spotipy.Spotify(auth_manager=auth_manager)

    try:
        playlist = sp.playlist(playlist_id)
        return {
            "name": playlist["name"],
            "owner": {
                "display_name": playlist["owner"]["display_name"],
                "id": playlist["owner"]["id"]
            },
            "followers": {
                "total": playlist["followers"]["total"]
            },
            "images": [
                {
                    "url": playlist["images"][0]["url"]
                }
            ]
        }
    except SpotifyException as e:
        raise HTTPException(status_code=e.http_status, detail=e.msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/playlist/{playlist_id}/tracks")
def get_playlist_tracks(playlist_id: str, request: Request):
    token_info = request.session.get('token_info', None)

    if token_info:
        sp = spotipy.Spotify(auth=token_info['access_token'])
    else:
        # Fallback to client credentials flow if user is not logged in
        auth_manager = spotipy.oauth2.SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
        sp = spotipy.Spotify(auth_manager=auth_manager)
        
    try:
        results = sp.playlist_tracks(playlist_id)
        tracks = results['items']
        while results['next']:
            results = sp.next(results)
            tracks.extend(results['items'])

        track_ids = [track['track']['id'] for track in tracks if track['track'] and track['track']['id']]
        
        audio_features = sp.audio_features(track_ids)
        audio_features = [af for af in audio_features if af]
        audio_features_map = {af['id']: af for af in audio_features}

        track_data = []
        for track in tracks:
            if track['track'] and track['track']['id'] in audio_features_map:
                track_info = track['track']
                af = audio_features_map[track_info['id']]
                track_data.append({
                    "id": track_info['id'],
                    "name": track_info['name'],
                    "artists": [artist['name'] for artist in track_info['artists']],
                    "preview_url": track_info['preview_url'],
                    "danceability": af['danceability'],
                    "energy": af['energy'],
                    "valence": af['valence'],
                    "tempo": af['tempo']
                })

        return track_data
    except SpotifyException as e:
        raise HTTPException(status_code=e.http_status, detail=e.msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))