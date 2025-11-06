from datetime import datetime
from typing import Dict

class HealthCheck:
    """Health check utility for the application"""
    
    @staticmethod
    def get_status() -> Dict:
        """Get the current health status of the application"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "uptime": datetime.now().timestamp() - STARTUP_TIME
        }
        
    @staticmethod
    def check_spotify_connection(sp) -> bool:
        """Check if Spotify API is accessible"""
        try:
            sp._get("me")
            return True
        except:
            return False
