import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';

const CardWrapper = styled(motion.div)`
  width: 300px;
  height: 400px;
  border-radius: 15px;
  background: #333;
  color: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  margin-top: 20px;
`;

const UserCard = ({ owner, topArtists }) => {
  return (
    <CardWrapper
      whileHover={{ scale: 1.05, boxShadow: "0px 10px 20px rgba(0,0,0,0.2)" }}
      transition={{ type: "spring", stiffness: 300 }}
    >
      <h2>{owner.display_name}</h2>
      <img src={owner.images?.[0]?.url} alt={owner.display_name} width="100" style={{ borderRadius: '50%' }} />
      <div>
        <h3>Top Artists</h3>
        <ul>
          {topArtists?.map(artist => (
            <li key={artist.id}>{artist.name}</li>
          ))}
        </ul>
      </div>
    </CardWrapper>
  );
};

export default UserCard;
