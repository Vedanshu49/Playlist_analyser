import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import Login from './Login';
import Dashboard from './Dashboard';
import NotFound from './NotFound';
import ErrorBoundary from './ErrorBoundary';
import Loading from './Loading';
import useAPI from './hooks/useAPI';
import styled from 'styled-components';

const AppContainer = styled.div`
    min-height: 100vh;
    background-color: #282c34;
`;

// Configure axios defaults
const API_URL = '';
axios.defaults.baseURL = API_URL;
axios.defaults.withCredentials = true;
axios.defaults.headers.common['X-CSRF-Token'] = true;

// Add response interceptor for error handling
axios.interceptors.response.use(
  response => response,
  error => {
    return Promise.reject(error);
  }
);

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const { fetchData, error: apiError } = useAPI();

  useEffect(() => {
    const controller = new AbortController();
    
    const fetchUser = async () => {
      try {
        const data = await fetchData('/api/me', {
          signal: controller.signal
        });
        setUser(data);
        setError(null);
      } catch (error) {
        if (!axios.isCancel(error)) {
          setUser(null);
          setError(apiError || 'Failed to fetch user data');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
    
    return () => controller.abort();
  }, [fetchData, apiError]);

  if (loading) {
    return <AppContainer><h1>Loading...</h1></AppContainer>;
  }

  if (loading) {
    return <Loading fullScreen text="Loading your profile..." />;
  }

  return (
    <ErrorBoundary>
      <Router>
        <AppContainer>
          <Routes>
            <Route 
              path="/" 
              element={user ? <Dashboard user={user} /> : <Login />} 
            />
            <Route
              path="/login"
              element={user ? <Navigate to="/" /> : <Login />}
            />
            <Route path="/error" element={<Login error={error} />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AppContainer>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
