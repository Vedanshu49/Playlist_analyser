from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.exceptions import SpotifyException

load_dotenv()

SPOTIPY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

app = FastAPI()

# CORS (Cross-Origin Resource Sharing) middleware
origins = [
    "http://localhost:3000",  # React app
    "https://your-app-name.vercel.app", # TODO: Replace with your Vercel app URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/api/playlist/{playlist_id}")
def get_playlist(playlist_id: str):
    try:
        client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        
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
def get_playlist_tracks(playlist_id: str):
    try:
        client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

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

@app.get("/api/user/{user_id}/top-playlists")
def get_user_top_playlists(user_id: str):
    try:
        client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        playlists = sp.user_playlists(user_id)

        top_playlists = []
        for playlist in playlists['items'][:3]:
            top_playlists.append({
                "name": playlist['name'],
                "id": playlist['id'],
                "images": playlist['images']
            })

        return top_playlists
    except SpotifyException as e:
        raise HTTPException(status_code=e.http_status, detail=e.msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{user_id}/top-artists")
# TODO: This is a workaround to get the user's top artists without requiring user authentication.
# The ideal solution would be to use the Spotify API's "Get User's Top Artists" endpoint,
# but that would require the Spotify Authorization Code Flow, which is a significant
# change to the application's architecture.
def get_user_top_artists(user_id: str):
    try:
        client_credentials_manager = SpotifyClientCredentials(client_id=SPOTIPY_CLIENT_ID, client_secret=SPOTIPY_CLIENT_SECRET)
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

        playlists = sp.user_playlists(user_id)
        
        artist_counts = {}

        for playlist in playlists['items']:
            results = sp.playlist_tracks(playlist['id'])
            tracks = results['items']
            while results['next']:
                results = sp.next(results)
                tracks.extend(results['items'])

            for item in tracks:
                track = item['track']
                if track:
                    for artist in track['artists']:
                        if artist['id']:
                            artist_id = artist['id']
                            if artist_id in artist_counts:
                                artist_counts[artist_id]['count'] += 1
                            else:
                                artist_counts[artist_id] = {'name': artist['name'], 'count': 1}

        sorted_artists = sorted(artist_counts.values(), key=lambda x: x['count'], reverse=True)
        
        top_artists = [{'name': artist['name']} for artist in sorted_artists[:3]]

        return top_artists
    except SpotifyException as e:
        raise HTTPException(status_code=e.http_status, detail=e.msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))