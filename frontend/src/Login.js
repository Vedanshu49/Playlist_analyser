import React from 'react';
import styled from 'styled-components';

const LoginContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background-color: #282c34;
`;

const Button = styled.a`
  padding: 15px 30px;
  font-size: 20px;
  background-color: #1db954; /* Spotify Green */
  color: white;
  border: none;
  border-radius: 50px;
  cursor: pointer;
  text-decoration: none;
  transition: background-color 0.3s ease;

  &:hover {
    background-color: #1ed760;
  }
`;

const Title = styled.h1`
    color: white;
    font-size: 3rem;
    margin-bottom: 1rem;
`;

const Subtitle = styled.p`
    color: #b3b3b3;
    font-size: 1.2rem;
    margin-bottom: 2rem;
`;

function Login() {
  return (
    <LoginContainer>
        <Title>Playlist Analyser</Title>
        <Subtitle>Please login with your Spotify account to continue</Subtitle>
      <Button href="/api/login">Login with Spotify</Button>
    </LoginContainer>
  );
}

export default Login;
