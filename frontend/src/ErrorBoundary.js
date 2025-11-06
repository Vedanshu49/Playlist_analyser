import React from 'react';
import styled from 'styled-components';

const ErrorContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
  background-color: #282c34;
  color: white;
  text-align: center;
`;

const ErrorTitle = styled.h1`
  color: #e74c3c;
  margin-bottom: 1rem;
`;

const ErrorMessage = styled.pre`
  background-color: rgba(231, 76, 60, 0.1);
  padding: 1rem;
  border-radius: 4px;
  margin: 1rem 0;
  max-width: 800px;
  overflow-x: auto;
`;

const ReloadButton = styled.button`
  padding: 0.5rem 1rem;
  font-size: 1rem;
  background-color: #1db954;
  color: white;
  border: none;
  border-radius: 20px;
  cursor: pointer;
  transition: background-color 0.3s;

  &:hover {
    background-color: #1ed760;
  }
`;

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
    
    // Log error to your preferred error tracking service
    console.error('Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <ErrorContainer>
          <ErrorTitle>Something went wrong</ErrorTitle>
          <p>We're sorry - something's gone wrong.</p>
          {process.env.NODE_ENV === 'development' && this.state.error && (
            <ErrorMessage>
              {this.state.error.toString()}
              <br />
              {this.state.errorInfo?.componentStack}
            </ErrorMessage>
          )}
          <ReloadButton onClick={() => window.location.reload()}>
            Reload Page
          </ReloadButton>
        </ErrorContainer>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
