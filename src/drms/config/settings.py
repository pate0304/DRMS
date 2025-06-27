"""
Settings and configuration for DRMS.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """DRMS configuration settings."""
    
    # Vector Database Settings
    vector_db_path: str = Field(default="./chroma_db", description="Path to ChromaDB storage")
    use_openai_embeddings: bool = Field(default=False, description="Use OpenAI embeddings instead of local model")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", description="Sentence transformer model")
    
    # Scraping Settings
    cache_dir: str = Field(default="./data/cache", description="Directory for caching scraped content")
    max_pages_per_library: int = Field(default=50, description="Maximum pages to scrape per library")
    scraping_delay: float = Field(default=1.0, description="Delay between requests in seconds")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    
    # API Settings
    api_host: str = Field(default="localhost", description="API host")
    api_port: int = Field(default=8000, description="API port")
    enable_cors: bool = Field(default=True, description="Enable CORS for API")
    
    # Logging Settings
    log_level: str = Field(default="INFO", description="Logging level")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    
    # Performance Settings
    max_concurrent_requests: int = Field(default=10, description="Maximum concurrent HTTP requests")
    chunk_size: int = Field(default=500, description="Text chunk size for embeddings")
    max_results: int = Field(default=20, description="Maximum search results to return")
    
    # Security Settings
    allowed_domains: list = Field(default_factory=list, description="Allowed domains for scraping")
    blocked_domains: list = Field(
        default_factory=lambda: ["malware.com", "phishing.com"], 
        description="Blocked domains"
    )
    
    class Config:
        env_file = ".env"
        env_prefix = "DRMS_"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Create directories if they don't exist
        Path(self.vector_db_path).mkdir(parents=True, exist_ok=True)
        Path(self.cache_dir).mkdir(parents=True, exist_ok=True)
        
        # Set OpenAI API key from environment if not provided
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
    
    @property
    def is_openai_configured(self) -> bool:
        """Check if OpenAI is properly configured."""
        return self.use_openai_embeddings and bool(self.openai_api_key)
    
    def get_cache_path(self, library_name: str) -> Path:
        """Get cache path for a specific library."""
        return Path(self.cache_dir) / f"{library_name}_cache.json"
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary."""
        return self.dict()
    
    @classmethod
    def from_file(cls, config_path: str) -> "Settings":
        """Load settings from a JSON file."""
        import json
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        return cls(**config_data)


# Global settings instance
_settings = None

def get_settings() -> Settings:
    """Get global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings