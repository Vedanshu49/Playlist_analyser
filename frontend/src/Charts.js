
import React, { useState, useEffect } from 'react';
import { RadialBarChart, RadialBar, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import styled, { keyframes } from 'styled-components';

const pulse = keyframes`
  0% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.4); }
  70% { box-shadow: 0 0 10px 20px rgba(255, 255, 255, 0); }
  100% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); }
`;

const PulsingGlow = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  animation: ${pulse} 2s infinite;
  z-index: 9999;
`;

const ChartsContainer = styled.div`
  display: flex;
  justify-content: space-around;
  width: 100%;
  margin-top: 20px;
`;

const ChartWrapper = styled.div`
  width: 30%;
  text-align: center;
`;

const TrackList = styled.ul`
  list-style: none;
  padding: 0;
  margin-top: 20px;
  width: 100%;
  max-height: 300px;
  overflow-y: auto;
`;

const TrackItem = styled.li`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px;
  border-bottom: 1px solid #444;
`;

const PlayButton = styled.button`
  background: #61dafb;
  border: none;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  cursor: pointer;
`;

const Charts = ({ trackData }) => {
  const [audio, setAudio] = useState(null);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    if (audio) {
      playing ? audio.play() : audio.pause();
    }
  }, [playing, audio]);

  const handlePlay = (previewUrl) => {
    if (audio && !audio.paused) {
      audio.pause();
      setPlaying(false);
    }

    if (previewUrl) {
      const newAudio = new Audio(previewUrl);
      setAudio(newAudio);
      setPlaying(true);
      newAudio.onended = () => setPlaying(false);
    }
  };

  if (!trackData) {
    return null;
  }

  const aggregatedData = {
    danceability: trackData.reduce((acc, t) => acc + t.danceability, 0) / trackData.length,
    energy: trackData.reduce((acc, t) => acc + t.energy, 0) / trackData.length,
    valence: trackData.reduce((acc, t) => acc + t.valence, 0) / trackData.length,
  };

  const radialData = [
    { name: 'Danceability', value: aggregatedData.danceability * 100, fill: '#8884d8' },
    { name: 'Energy', value: aggregatedData.energy * 100, fill: '#83a6ed' },
    { name: 'Valence', value: aggregatedData.valence * 100, fill: '#8dd1e1' },
  ];

  const tempoData = trackData.map(t => ({ tempo: t.tempo }));

  return (
    <>
      {playing && <PulsingGlow />}
      <ChartsContainer>
        <ChartWrapper>
          <h3>Audio Features</h3>
          <ResponsiveContainer width="100%" height={300}>
            <RadialBarChart innerRadius="10%" outerRadius="80%" data={radialData} startAngle={180} endAngle={0}>
              <RadialBar minAngle={15} label={{ position: 'insideStart', fill: '#fff' }} background clockWise dataKey="value" />
              <Legend iconSize={10} width={120} height={140} layout="vertical" verticalAlign="middle" wrapperStyle={{ top: '50%', right: 0, transform: 'translate(0, -50%)' }} />
            </RadialBarChart>
          </ResponsiveContainer>
        </ChartWrapper>
        <ChartWrapper>
          <h3>Tempo Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={tempoData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="tempo" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="tempo" fill="#8884d8" />
            </BarChart>
          </ResponsiveContainer>
        </ChartWrapper>
        <ChartWrapper>
          <h3>Tracks</h3>
          <TrackList>
            {trackData.map(track => (
              <TrackItem key={track.id}>
                <span>{track.name}</span>
                {track.preview_url && <PlayButton onClick={() => handlePlay(track.preview_url)} />}
              </TrackItem>
            ))}
          </TrackList>
        </ChartWrapper>
      </ChartsContainer>
    </>
  );
};

export default Charts;