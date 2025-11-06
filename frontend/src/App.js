
import React, { useState } from 'react';
import axios from 'axios';
import styled from 'styled-components';
import UserCard from './UserCard';
import Charts from './Charts';

const AppContainer = styled.div`
  text-align: center;
  background: ${({ aura }) => (aura ? auraGradients[aura] : '#282c34')};
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  font-size: calc(10px + 2vmin);
  color: white;
  transition: background 0.5s ease;
`;

const auraGradients = {
  'High-Energy Party': 'linear-gradient(to right, #ff7e5f, #feb47b)',
  'Happy & Energetic': 'linear-gradient(to right, #ffc371, #ff5f6d)',
  'Chill & Melancholic': 'linear-gradient(to right, #3a6186, #89253e)',
  'Funky & Groovy': 'linear-gradient(to right, #ff6e7f, #bfe9ff)',
  'Mellow Vibes': 'linear-gradient(to right, #485563, #29323c)',
};

const Input = styled.input`
  padding: 10px;
  font-size: 16px;
  border: 2px solid #61dafb;
  border-radius: 5px;
  margin-right: 10px;
`;

const Button = styled.button`
  padding: 10px 20px;
  font-size: 16px;
  background-color: #61dafb;
  color: #282c34;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: #4a9cb0;
  }
`;

const PlaylistInfo = styled.div`
  margin-top: 20px;
  padding: 20px;
  border: 1px solid #61dafb;
  border-radius: 10px;
  text-align: left;
`;

function App() {
  const [playlistUrl, setPlaylistUrl] = useState('');
  const [playlistData, setPlaylistData] = useState(null);
  const [trackData, setTrackData] = useState(null);
  const [topPlaylists, setTopPlaylists] = useState(null);
  const [topArtists, setTopArtists] = useState(null);
  const [error, setError] = useState(null);
  const [aura, setAura] = useState('');

  const calculateAura = (tracks) => {
    if (!tracks || tracks.length === 0) return '';

    let avgDanceability = 0;
    let avgEnergy = 0;
    let avgValence = 0;

    tracks.forEach(track => {
      avgDanceability += track.danceability;
      avgEnergy += track.energy;
      avgValence += track.valence;
    });

    avgDanceability /= tracks.length;
    avgEnergy /= tracks.length;
    avgValence /= tracks.length;

    if (avgEnergy > 0.7 && avgDanceability > 0.7) {
      return 'High-Energy Party';
    } else if (avgValence > 0.7 && avgEnergy > 0.5) {
      return 'Happy & Energetic';
    } else if (avgEnergy < 0.4 && avgValence < 0.4) {
      return 'Chill & Melancholic';
    } else if (avgDanceability > 0.6 && avgValence > 0.5) {
      return 'Funky & Groovy';
    } else {
      return 'Mellow Vibes';
    }
  };


  const extractPlaylistId = (url) => {
    const match = url.match(/playlist\/(\w+)/);
    return match ? match[1] : null;
  };

  const handleFetchPlaylist = async () => {
    const extractedId = extractPlaylistId(playlistUrl);
    if (!extractedId) {
      setError('Invalid Spotify Playlist URL');
      return;
    }

    try {
      const response = await axios.get(`http://127.0.0.1:8000/api/playlist/${extractedId}`);
      if (response.data.error) {
        setError(response.data.error);
        setPlaylistData(null);
      } else {
        setPlaylistData(response.data);
        setError(null);

        const tracksResponse = await axios.get(`http://127.0.0.1:8000/api/playlist/${extractedId}/tracks`);
        setTrackData(tracksResponse.data);
        const calculatedAura = calculateAura(tracksResponse.data);
        setAura(calculatedAura);


        const ownerId = response.data.owner.id;
        const topPlaylistsResponse = await axios.get(`http://127.0.0.1:8000/api/user/${ownerId}/top-playlists`);
        setTopPlaylists(topPlaylistsResponse.data);

        const topArtistsResponse = await axios.get(`http://127.0.0.1:8000/api/user/${ownerId}/top-artists`);
        setTopArtists(topArtistsResponse.data);

      }
    } catch (err) {
      setError('Could not fetch playlist. Please check the URL and try again.');
      setPlaylistData(null);
    }
  };

  return (
    <AppContainer aura={aura}>
      <h1>Playlist Analyzer</h1>
      <div>
        <Input
          type="text"
          value={playlistUrl}
          onChange={(e) => setPlaylistUrl(e.target.value)}
          placeholder="Enter Spotify Playlist Link"
        />
        <Button onClick={handleFetchPlaylist}>Fetch Playlist</Button>
      </div>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {playlistData && (
        <PlaylistInfo>
          <h2>{playlistData.name}</h2>
          <p>{playlistData.followers.total} Followers</p>
          <img src={playlistData.images[0]?.url} alt="Playlist Cover" width="200" />
        </PlaylistInfo>
      )}
      {aura && <h3>Playlist Aura: {aura}</h3>}
      {playlistData && topArtists && topPlaylists && (
        <UserCard owner={playlistData.owner} topPlaylists={topPlaylists} topArtists={topArtists} />
      )}
      {trackData && <Charts trackData={trackData} />}
    </AppContainer>
  );
}

export default App;
