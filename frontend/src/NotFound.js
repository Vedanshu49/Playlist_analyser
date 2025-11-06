import React from 'react';
import styled from 'styled-components';
import { useNavigate } from 'react-router-dom';

const NotFoundContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  text-align: center;
  background-color: #282c34;
  color: white;
`;

const Title = styled.h1`
  font-size: 4rem;
  margin-bottom: 1rem;
`;

const Message = styled.p`
  font-size: 1.5rem;
  margin-bottom: 2rem;
`;

const Button = styled.button`
  padding: 1rem 2rem;
  font-size: 1.2rem;
  background-color: #1db954;
  color: white;
  border: none;
  border-radius: 25px;
  cursor: pointer;
  transition: background-color 0.3s;

  &:hover {
    background-color: #1ed760;
  }
`;

function NotFound() {
  const navigate = useNavigate();

  return (
    <NotFoundContainer>
      <Title>404</Title>
      <Message>Oops! The page you're looking for doesn't exist.</Message>
      <Button onClick={() => navigate('/')}>Back to Home</Button>
    </NotFoundContainer>
  );
}

export default NotFound;
