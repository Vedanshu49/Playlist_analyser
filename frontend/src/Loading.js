import React from 'react';
import styled, { keyframes } from 'styled-components';

const spin = keyframes`
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
`;

const LoaderContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: ${props => props.fullScreen ? '100vh' : '200px'};
`;

const Spinner = styled.div`
  width: 40px;
  height: 40px;
  border: 4px solid #1db954;
  border-top: 4px solid transparent;
  border-radius: 50%;
  animation: ${spin} 1s linear infinite;
`;

const LoadingText = styled.p`
  margin-top: 1rem;
  color: #1db954;
  font-size: 1.2rem;
`;

function Loading({ text = 'Loading...', fullScreen = false }) {
  return (
    <LoaderContainer fullScreen={fullScreen}>
      <Spinner />
      <LoadingText>{text}</LoadingText>
    </LoaderContainer>
  );
}

export default Loading;
