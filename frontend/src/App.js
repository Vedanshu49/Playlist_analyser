import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Login from './Login';
import Dashboard from './Dashboard';
import styled from 'styled-components';

const AppContainer = styled.div`
    min-height: 100vh;
    background-color: #282c34;
`;

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const response = await axios.get('http://127.0.0.1:8000/api/me', { withCredentials: true });
        setUser(response.data);
      } catch (error) {
        setUser(null);
      }
      setLoading(false);
    };

    fetchUser();
  }, []);

  if (loading) {
    return <AppContainer><h1>Loading...</h1></AppContainer>;
  }

  return (
    <AppContainer>
      {user ? <Dashboard user={user} /> : <Login />}
    </AppContainer>
  );
}

export default App;
