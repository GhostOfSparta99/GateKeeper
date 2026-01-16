import os
import sys
import errno
import time
import threading
from fuse import FUSE, FuseOSError, Operations
import requests

# --- CONFIGURATION ---
SUPABASE_URL = "https://lwstwekouztglkoescog.supabase.co"
SUPABASE_KEY = "sb_publishable_dmwRDftSHwm7PlapTWGlIg_rVHCrN9y"
SOURCE_DIR = "my_hidden_data"
MOUNT_POINT = "S:"

# Helper class to mimic Supabase client using requests (High Performance Adapted)
class NativeSupabase:
    def __init__(self, url, key):
        self.base_url = f"{url}/rest/v1"
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }

    def upsert_file(self, filename):
        """Upsert a file into file_locks (POST with merge-duplicates)"""
        url = f"{self.base_url}/file_locks?on_conflict=filename"
        headers = self.headers.copy()
        headers["Prefer"] = "resolution=merge-duplicates"
        payload = {"filename": filename}
        try:
            requests.post(url, headers=headers, json=payload, timeout=2.0)
        except Exception as e:
            print(f"   ⚠️ Sync Upload Warning: {e}")

    def delete_file(self, filename):
        """Delete a file from file_locks"""
        url = f"{self.base_url}/file_locks?filename=eq.{filename}"
        try:
            requests.delete(url, headers=self.headers, timeout=2.0)
        except Exception as e:
            print(f"   ⚠️ Sync Delete Warning: {e}")

    def rename_file(self, old_name, new_name):
        """Update filename in file_locks"""
        url = f"{self.base_url}/file_locks?filename=eq.{old_name}"
        payload = {"filename": new_name}
        try:
            requests.patch(url, headers=self.headers, json=payload, timeout=2.0)
        except Exception as e:
            print(f"   ⚠️ Sync Rename Warning: {e}")

    def get_all_locks(self):
        """Fetch ALL lock statuses at once"""
        url = f"{self.base_url}/file_locks?select=filename,is_locked"
        try:
            r = requests.get(url, headers=self.headers, timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except:
            return []
        return []

    def update_last_accessed(self, filename):
        """Update last_accessed timestamp"""
        url = f"{self.base_url}/file_locks?filename=eq.{filename}"
        payload = {"last_accessed": "now()"}
        try:
            requests.patch(url, headers=self.headers, json=payload, timeout=0.5)
        except:
            pass

    def create_new_file(self, filename):
        """Insert new file record"""
        url = f"{self.base_url}/file_locks"
        payload = {"filename": filename, "is_locked": False}
        try:
            requests.post(url, headers=self.headers, json=payload, timeout=1.0)
        except:
            pass

# Initialize "Client"
db = NativeSupabase(SUPABASE_URL, SUPABASE_KEY)

class Gatekeeper(Operations):
    def __init__(self, root):
        self.root = root
        # LOCAL CACHE: Stores 'filename': is_locked (True/False)
        self.lock_cache = {} 
        self.running = True
        
        # Start Background Thread (Syncs Files & Locks)
        self.bg_thread = threading.Thread(target=self._background_syncer, daemon=True)
        self.bg_thread.start()

    def _background_syncer(self):
        """
        Runs in background: 
        1. Pushes local file changes (New/Deleted) to DB
        2. Pulls lock status from DB
        """
        print("🔄 Background Sync Active: Monitoring File System & Cloud...")
        while self.running:
            try:
                # A. SCAN LOCAL FILES
                if os.path.exists(self.root):
                    local_files = set(f for f in os.listdir(self.root) 
                                    if os.path.isfile(os.path.join(self.root, f)))
                else:
                    local_files = set()

                # B. FETCH REMOTE FILES
                remote_data = db.get_all_locks()
                remote_map = {row['filename']: row['is_locked'] for row in remote_data}
                remote_files = set(remote_map.keys())

                # C. SYNC: UPLOAD NEW FILES (Local -> Cloud)
                files_to_add = local_files - remote_files
                for filename in files_to_add:
                    print(f"   [SYNC] Found new file: {filename} -> Uploading to DB")
                    db.create_new_file(filename)

                # D. SYNC: REMOVE DELETED FILES (Cloud -> Clean DB)
                files_to_remove = remote_files - local_files
                for filename in files_to_remove:
                    print(f"   [SYNC] File deleted locally: {filename} -> Removing from DB")
                    db.delete_file(filename)

                # E. UPDATE LOCK CACHE (For Cloud -> Local locking)
                # We refresh our cache with the latest valid list
                self.lock_cache = remote_map
                
            except Exception as e:
                print(f"⚠️ Sync Loop Error: {e}")
            
            # Run this check every 2 seconds
            time.sleep(2.0)

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    # --- ATTRIBUTES ---
    def getattr(self, path, fh=None):
        full_path = self._full_path(path)
        try:
            st = os.lstat(full_path)
            return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                        'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))
        except OSError:
            raise FuseOSError(errno.ENOENT)

    # --- READ DIRECTORY ---
    def readdir(self, path, fh):
        full_path = self._full_path(path)
        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    # --- OPEN FILE (Now Instant!) ---
    def open(self, path, flags):
        full_path = self._full_path(path)
        filename = os.path.basename(path)

        # 1. READ FROM LOCAL CACHE (Zero Latency)
        # If file is not in cache, assume UNLOCKED (False) until proven otherwise
        is_locked = self.lock_cache.get(filename, False)

        if is_locked:
            print(f"🔒 [BLOCKED CACHED] Access denied to: {filename}")
            raise FuseOSError(errno.EACCES)
        
        # print(f"✅ [ALLOWED] {filename}") # Uncomment for verbose logs

        # Optional: Update last accessed in background
        threading.Thread(target=db.update_last_accessed, args=(filename,)).start()

        # === WINDOWS COMPATIBILITY FIX ===
        access_flags = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        final_flags = flags & access_flags
        final_flags |= os.O_BINARY

        return os.open(full_path, final_flags)

    # --- READ / WRITE / CREATE ---
    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def create(self, path, mode, fi=None):
        full_path = self._full_path(path)
        filename = os.path.basename(path)
        
        # Add to local cache immediately so we don't block ourselves
        self.lock_cache[filename] = False
        
        # Async upload to DB (don't wait for it)
        threading.Thread(target=db.create_new_file, args=(filename,)).start()
        
        return os.open(full_path, os.O_WRONLY | os.O_CREAT | os.O_BINARY, mode)

    # --- UNLINK / DELETE (Instant DB Update) ---
    def unlink(self, path):
        full_path = self._full_path(path)
        filename = os.path.basename(path)

        print(f"🗑️  Deleting file: {filename}")
        
        # 1. Delete actual file
        os.unlink(full_path)
        
        # 2. Remove from DB immediately
        threading.Thread(target=db.delete_file, args=(filename,)).start()
        
        # 3. Remove from local cache
        if filename in self.lock_cache:
            del self.lock_cache[filename]

    # --- RENAME (Update DB) ---
    def rename(self, old, new):
        full_old = self._full_path(old)
        full_new = self._full_path(new)
        
        old_name = os.path.basename(old)
        new_name = os.path.basename(new)

        print(f"✏️  Renaming: {old_name} -> {new_name}")
        
        # 1. Rename actual file
        os.rename(full_old, full_new)
        
        # 2. Update DB (Update the filename field)
        threading.Thread(target=db.rename_file, args=(old_name, new_name)).start()

    def release(self, path, fh):
        return os.close(fh)
    
    def flush(self, path, fh):
        return os.fsync(fh)

if __name__ == '__main__':
    if not os.path.exists(SOURCE_DIR):
        os.makedirs(SOURCE_DIR)
    
    print(f"🚀 Gatekeeper v2.0 (Auto-Sync) Active on {MOUNT_POINT}")
    try:
        FUSE(Gatekeeper(SOURCE_DIR), MOUNT_POINT, foreground=True, nothreads=False)
    except Exception as e:
        print(f"Error: {e}")
