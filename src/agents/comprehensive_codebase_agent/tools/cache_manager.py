import os
import json
import hashlib
import pickle
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Dict, List, Union
from dataclasses import dataclass, asdict
from agents import function_tool


@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: datetime
    file_path: str
    file_mtime: float
    analysis_type: str
    size_bytes: int
    expires_at: Optional[datetime] = None


class CacheManager:
    """Manages caching for codebase analysis results"""
    
    def __init__(self, cache_dir: str = "./cache", memory_limit_mb: int = 100):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Memory cache for small items
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.memory_limit_bytes = memory_limit_mb * 1024 * 1024
        self.current_memory_usage = 0
        
        # SQLite database for metadata
        self.db_path = self.cache_dir / "cache_metadata.db"
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for cache metadata"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache_entries (
                    key TEXT PRIMARY KEY,
                    file_path TEXT,
                    file_mtime REAL,
                    analysis_type TEXT,
                    created_at TEXT,
                    expires_at TEXT,
                    size_bytes INTEGER,
                    storage_type TEXT,
                    file_location TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_path ON cache_entries(file_path)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_analysis_type ON cache_entries(analysis_type)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at ON cache_entries(expires_at)
            """)
    
    def _generate_cache_key(self, file_path: str, analysis_type: str, file_mtime: float, **kwargs) -> str:
        """Generate a unique cache key"""
        key_data = f"{file_path}_{file_mtime}_{analysis_type}_{str(sorted(kwargs.items()))}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]
    
    def _get_file_mtime(self, file_path: str) -> Optional[float]:
        """Get file modification time"""
        try:
            return os.path.getmtime(file_path)
        except (OSError, FileNotFoundError):
            return None
    
    def _estimate_size(self, data: Any) -> int:
        """Estimate the size of data in bytes"""
        try:
            if isinstance(data, str):
                return len(data.encode('utf-8'))
            elif isinstance(data, (dict, list)):
                return len(json.dumps(data, default=str).encode('utf-8'))
            else:
                return len(pickle.dumps(data))
        except:
            return 1024  # Default estimate
    
    def _should_store_in_memory(self, size_bytes: int) -> bool:
        """Determine if item should be stored in memory vs file"""
        small_item_threshold = 50 * 1024  # 50KB
        return size_bytes < small_item_threshold and self.current_memory_usage + size_bytes < self.memory_limit_bytes
    
    def _cleanup_memory_cache(self):
        """Remove oldest items from memory cache when limit exceeded"""
        if self.current_memory_usage <= self.memory_limit_bytes:
            return
        
        # Sort by creation time, remove oldest
        sorted_entries = sorted(
            self.memory_cache.items(),
            key=lambda x: x[1].created_at
        )
        
        while self.current_memory_usage > self.memory_limit_bytes and sorted_entries:
            key, entry = sorted_entries.pop(0)
            del self.memory_cache[key]
            self.current_memory_usage -= entry.size_bytes
    
    def _save_to_disk(self, key: str, data: Any) -> str:
        """Save data to disk and return file path"""
        file_path = self.cache_dir / f"{key}.cache"
        
        try:
            if isinstance(data, str):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(data)
            else:
                with open(file_path, 'wb') as f:
                    pickle.dump(data, f)
            
            return str(file_path)
        except Exception as e:
            raise Exception(f"Failed to save cache to disk: {e}")
    
    def _load_from_disk(self, file_path: str) -> Any:
        """Load data from disk"""
        try:
            # Try text first
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except UnicodeDecodeError:
                # Fall back to pickle
                with open(file_path, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            raise Exception(f"Failed to load cache from disk: {e}")
    
    def get(self, file_path: str, analysis_type: str, **kwargs) -> Optional[Any]:
        """Get cached result for a file and analysis type"""
        file_mtime = self._get_file_mtime(file_path)
        if file_mtime is None:
            return None  # File doesn't exist
        
        cache_key = self._generate_cache_key(file_path, analysis_type, file_mtime, **kwargs)
        
        # Check memory cache first
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            
            # Check if expired
            if entry.expires_at and datetime.now() > entry.expires_at:
                del self.memory_cache[cache_key]
                self.current_memory_usage -= entry.size_bytes
                return None
            
            return entry.value
        
        # Check database for disk cache
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM cache_entries WHERE key = ?",
                (cache_key,)
            )
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Parse row data
            _, db_file_path, db_file_mtime, db_analysis_type, created_at_str, expires_at_str, size_bytes, storage_type, file_location = row
            
            # Check if expired
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                if datetime.now() > expires_at:
                    self._delete_cache_entry(cache_key)
                    return None
            
            # Check if file has been modified
            if db_file_mtime != file_mtime:
                self._delete_cache_entry(cache_key)
                return None
            
            # Load from disk
            try:
                data = self._load_from_disk(file_location)
                
                # Maybe promote to memory cache if small enough
                if self._should_store_in_memory(size_bytes):
                    entry = CacheEntry(
                        key=cache_key,
                        value=data,
                        created_at=datetime.fromisoformat(created_at_str),
                        file_path=file_path,
                        file_mtime=file_mtime,
                        analysis_type=analysis_type,
                        size_bytes=size_bytes,
                        expires_at=datetime.fromisoformat(expires_at_str) if expires_at_str else None
                    )
                    self.memory_cache[cache_key] = entry
                    self.current_memory_usage += size_bytes
                    self._cleanup_memory_cache()
                
                return data
                
            except Exception:
                # Cache file corrupted, remove entry
                self._delete_cache_entry(cache_key)
                return None
    
    def set(self, file_path: str, analysis_type: str, data: Any, ttl_hours: int = 24, **kwargs) -> bool:
        """Cache analysis result"""
        file_mtime = self._get_file_mtime(file_path)
        if file_mtime is None:
            return False  # File doesn't exist
        
        cache_key = self._generate_cache_key(file_path, analysis_type, file_mtime, **kwargs)
        size_bytes = self._estimate_size(data)
        created_at = datetime.now()
        expires_at = created_at + timedelta(hours=ttl_hours) if ttl_hours > 0 else None
        
        try:
            if self._should_store_in_memory(size_bytes):
                # Store in memory
                entry = CacheEntry(
                    key=cache_key,
                    value=data,
                    created_at=created_at,
                    file_path=file_path,
                    file_mtime=file_mtime,
                    analysis_type=analysis_type,
                    size_bytes=size_bytes,
                    expires_at=expires_at
                )
                
                self.memory_cache[cache_key] = entry
                self.current_memory_usage += size_bytes
                self._cleanup_memory_cache()
                
                storage_type = "memory"
                file_location = ""
            else:
                # Store on disk
                file_location = self._save_to_disk(cache_key, data)
                storage_type = "disk"
            
            # Update database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cache_entries 
                    (key, file_path, file_mtime, analysis_type, created_at, expires_at, size_bytes, storage_type, file_location)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cache_key,
                    file_path,
                    file_mtime,
                    analysis_type,
                    created_at.isoformat(),
                    expires_at.isoformat() if expires_at else None,
                    size_bytes,
                    storage_type,
                    file_location
                ))
            
            return True
            
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def _delete_cache_entry(self, cache_key: str):
        """Delete a cache entry completely"""
        # Remove from memory
        if cache_key in self.memory_cache:
            entry = self.memory_cache[cache_key]
            del self.memory_cache[cache_key]
            self.current_memory_usage -= entry.size_bytes
        
        # Remove from database and disk
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT file_location FROM cache_entries WHERE key = ?",
                (cache_key,)
            )
            row = cursor.fetchone()
            
            if row and row[0]:  # Has disk file
                try:
                    os.remove(row[0])
                except OSError:
                    pass
            
            conn.execute("DELETE FROM cache_entries WHERE key = ?", (cache_key,))
    
    def clear_expired(self) -> int:
        """Clear expired cache entries"""
        now = datetime.now()
        count = 0
        
        # Clear from memory
        expired_keys = [
            key for key, entry in self.memory_cache.items()
            if entry.expires_at and now > entry.expires_at
        ]
        
        for key in expired_keys:
            entry = self.memory_cache[key]
            del self.memory_cache[key]
            self.current_memory_usage -= entry.size_bytes
            count += 1
        
        # Clear from database/disk
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT key, file_location FROM cache_entries WHERE expires_at < ?",
                (now.isoformat(),)
            )
            
            for key, file_location in cursor.fetchall():
                if file_location:
                    try:
                        os.remove(file_location)
                    except OSError:
                        pass
                count += 1
            
            conn.execute("DELETE FROM cache_entries WHERE expires_at < ?", (now.isoformat(),))
        
        return count
    
    def clear_file_cache(self, file_path: str) -> int:
        """Clear all cache entries for a specific file"""
        count = 0
        
        # Clear from memory
        keys_to_remove = [
            key for key, entry in self.memory_cache.items()
            if entry.file_path == file_path
        ]
        
        for key in keys_to_remove:
            entry = self.memory_cache[key]
            del self.memory_cache[key]
            self.current_memory_usage -= entry.size_bytes
            count += 1
        
        # Clear from database/disk
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT key, file_location FROM cache_entries WHERE file_path = ?",
                (file_path,)
            )
            
            for key, file_location in cursor.fetchall():
                if file_location:
                    try:
                        os.remove(file_location)
                    except OSError:
                        pass
                count += 1
            
            conn.execute("DELETE FROM cache_entries WHERE file_path = ?", (file_path,))
        
        return count
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*), SUM(size_bytes) FROM cache_entries")
            total_entries, total_disk_bytes = cursor.fetchone()
            
            cursor = conn.execute("SELECT storage_type, COUNT(*) FROM cache_entries GROUP BY storage_type")
            storage_breakdown = dict(cursor.fetchall())
        
        memory_entries = len(self.memory_cache)
        memory_bytes = self.current_memory_usage
        
        return {
            'total_entries': (total_entries or 0) + memory_entries,
            'memory_entries': memory_entries,
            'disk_entries': total_entries or 0,
            'memory_usage_bytes': memory_bytes,
            'memory_usage_mb': round(memory_bytes / (1024 * 1024), 2),
            'disk_usage_bytes': total_disk_bytes or 0,
            'disk_usage_mb': round((total_disk_bytes or 0) / (1024 * 1024), 2),
            'storage_breakdown': storage_breakdown
        }


# Global cache manager instance
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


@function_tool
async def get_cached_analysis(
    file_path: str,
    analysis_type: str
) -> Optional[str]:
    """
    Get cached analysis result for a file.
    
    Args:
        file_path: Path to the file
        analysis_type: Type of analysis (e.g., 'functions', 'api_endpoints', 'dependencies')
    
    Returns:
        Cached result as string, or None if not found/expired
    """
    try:
        cache_manager = get_cache_manager()
        result = cache_manager.get(file_path, analysis_type)
        
        if result is None:
            return "❌ No cached result found or cache expired"
        
        return f"✅ **Cached Result Found**\n\n{result}"
        
    except Exception as e:
        return f"❌ Error accessing cache: {str(e)}"


@function_tool
async def cache_analysis_result(
    file_path: str,
    analysis_type: str,
    result_data: str,
    ttl_hours: int = 24
) -> str:
    """
    Cache an analysis result.
    
    Args:
        file_path: Path to the file
        analysis_type: Type of analysis
        result_data: The analysis result to cache
        ttl_hours: Time to live in hours (0 = no expiration)
    
    Returns:
        Success/failure message
    """
    try:
        cache_manager = get_cache_manager()
        success = cache_manager.set(file_path, analysis_type, result_data, ttl_hours)
        
        if success:
            size_mb = len(result_data.encode('utf-8')) / (1024 * 1024)
            return f"✅ **Analysis cached successfully**\n- File: {file_path}\n- Type: {analysis_type}\n- Size: {size_mb:.2f} MB\n- TTL: {ttl_hours} hours"
        else:
            return f"❌ Failed to cache analysis result for {file_path}"
            
    except Exception as e:
        return f"❌ Error caching result: {str(e)}"


@function_tool
async def cache_cleanup() -> str:
    """
    Clean up expired cache entries and get cache statistics.
    
    Returns:
        Cleanup summary and cache statistics
    """
    try:
        cache_manager = get_cache_manager()
        
        # Clean up expired entries
        expired_count = cache_manager.clear_expired()
        
        # Get current stats
        stats = cache_manager.get_cache_stats()
        
        output = f"""# 🧹 Cache Cleanup Summary

## 🗑️ Cleanup Results
- **Expired entries removed**: {expired_count}

## 📊 Current Cache Statistics
- **Total entries**: {stats['total_entries']:,}
- **Memory entries**: {stats['memory_entries']:,}
- **Disk entries**: {stats['disk_entries']:,}
- **Memory usage**: {stats['memory_usage_mb']:.1f} MB
- **Disk usage**: {stats['disk_usage_mb']:.1f} MB

## 💾 Storage Breakdown
"""
        
        for storage_type, count in stats.get('storage_breakdown', {}).items():
            output += f"- **{storage_type.title()}**: {count:,} entries\n"
        
        return output
        
    except Exception as e:
        return f"❌ Error during cache cleanup: {str(e)}"


@function_tool
async def clear_file_cache(file_path: str) -> str:
    """
    Clear all cache entries for a specific file.
    
    Args:
        file_path: Path to the file whose cache should be cleared
    
    Returns:
        Cleanup summary
    """
    try:
        cache_manager = get_cache_manager()
        cleared_count = cache_manager.clear_file_cache(file_path)
        
        return f"✅ **File cache cleared**\n- File: {file_path}\n- Entries removed: {cleared_count}"
        
    except Exception as e:
        return f"❌ Error clearing file cache: {str(e)}"