import { useState, useCallback } from 'react';
import axios from 'axios';

const MAX_RETRIES = 3;
const INITIAL_RETRY_DELAY = 1000;

export const validateSpotifyUrl = (url) => {
  if (!url) return false;
  
  try {
    const parsedUrl = new URL(url);
    if (!parsedUrl.hostname.includes('spotify.com')) {
      return false;
    }
    
    // Extract playlist ID
    const match = url.match(/playlist[/:]([a-zA-Z0-9]{22})/);
    return match ? match[1] : false;
  } catch (e) {
    return false;
  }
};

const useAPI = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchWithRetry = useCallback(async (
    url,
    options = {},
    retryCount = 0,
    delay = INITIAL_RETRY_DELAY
  ) => {
    try {
      const response = await axios({
        ...options,
        url,
        withCredentials: true
      });
      setError(null);
      return response.data;
    } catch (err) {
      // Don't retry on client errors (4xx)
      if (err.response?.status >= 400 && err.response?.status < 500) {
        throw err;
      }
      
      // Retry on server errors or network issues
      if (retryCount < MAX_RETRIES) {
        await new Promise(resolve => setTimeout(resolve, delay));
        return fetchWithRetry(
          url,
          options,
          retryCount + 1,
          delay * 2 // Exponential backoff
        );
      }
      
      throw err;
    }
  }, []);

  const fetchData = useCallback(async (url, options = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await fetchWithRetry(url, options);
      return data;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || 'An error occurred';
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [fetchWithRetry]);

  return {
    loading,
    error,
    fetchData,
    validateSpotifyUrl
  };
};

export default useAPI;
