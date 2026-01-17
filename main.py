import os
import sys
import errno
import time
import threading
from fuse import FUSE, FuseOSError, Operations
import requests

# --- CONFIGURATION ---
SUPABASE_URL = "https://zkpgilfposjkshvtteto.supabase.co"
SUPABASE_KEY = "sb_publishable_B04aDmwXy7U9i3SCvxggnw_wYLiIz2z"
SOURCE_DIR = "my_hidden_data"
MOUNT_POINT = "S:"

# --- HELPER: Database Client ---
class NativeSupabase:
    def __init__(self, url, key):
        self.base_url = f"{url}/rest/v1"
        # Standard Headers (For Reading)
        self.read_headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        # Write Headers (For Fast Updates)
        self.write_headers = self.read_headers.copy()
        self.write_headers["Prefer"] = "return=minimal"

    def get_all_locks(self):
        """Fetch ALL lock statuses at once"""
        # CRITICAL FIX: Use read_headers (NO 'return=minimal')
        url = f"{self.base_url}/file_locks?select=filename,is_locked&limit=1000"
        try:
            r = requests.get(url, headers=self.read_headers, timeout=5.0)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"   ⚠️ Sync Fetch Error: {e}")
        return []

    def insert_file(self, filename):
        """Insert new file record"""
        url = f"{self.base_url}/file_locks"
        payload = {"filename": filename, "is_locked": False}
        try:
            # Use 'resolution=ignore-duplicates' to prevent errors
            headers = self.write_headers.copy()
            headers["Prefer"] = "resolution=ignore-duplicates,return=minimal"
            requests.post(url, headers=headers, json=payload, timeout=2.0)
        except Exception as e:
            print(f"   ⚠️ Sync Insert Error: {e}")

    def delete_file(self, filename):
        """Delete file record"""
        url = f"{self.base_url}/file_locks?filename=eq.{filename}"
        try:
            requests.delete(url, headers=self.write_headers, timeout=2.0)
        except Exception as e:
            print(f"   ⚠️ Sync Delete Error: {e}")

    def rename_file(self, old_name, new_name):
        url = f"{self.base_url}/file_locks?filename=eq.{old_name}"
        payload = {"filename": new_name}
        try:
            requests.patch(url, headers=self.write_headers, json=payload, timeout=2.0)
        except:
            pass
            
    def update_last_accessed(self, filename):
        url = f"{self.base_url}/file_locks?filename=eq.{filename}"
        payload = {"last_accessed": "now()"}
        try:
            requests.patch(url, headers=self.write_headers, json=payload, timeout=0.5)
        except:
            pass

# Initialize Client
db = NativeSupabase(SUPABASE_URL, SUPABASE_KEY)

# --- FUSE FILESYSTEM ---
class Gatekeeper(Operations):
    def __init__(self, root):
        self.root = root
        self.lock_cache = {} 
        self.running = True
        
        # Start Background Thread
        self.bg_thread = threading.Thread(target=self._background_syncer, daemon=True)
        self.bg_thread.start()

    def _is_valid_file(self, filename):
        """FILTER: Ignore temp files"""
        if filename.startswith("~$"): return False
        if filename.startswith("."): return False
        if filename.lower() == "desktop.ini": return False
        if filename.lower().endswith(".tmp"): return False
        return True

    def _background_syncer(self):
        print("🔄 Background Sync Active...")
        while self.running:
            try:
                # 1. SCAN LOCAL FILES
                if os.path.exists(self.root):
                    root_files = set(f for f in os.listdir(self.root) 
                                   if os.path.isfile(os.path.join(self.root, f)) 
                                   and self._is_valid_file(f))
                else:
                    root_files = set()

                # 2. FETCH REMOTE FILES
                remote_data = db.get_all_locks()
                remote_map = {row['filename'].lower(): row['is_locked'] for row in remote_data}
                remote_files = set(remote_map.keys())

                # Update Cache
                self.lock_cache = remote_map

                # 3. SYNC: UPLOAD NEW
                files_to_add = root_files - remote_files
                for filename in files_to_add:
                    print(f"   [SYNC] Found new file: {filename}")
                    db.insert_file(filename)

                # 4. SYNC: REMOVE DELETED
                files_to_remove = remote_files - root_files
                for filename in files_to_remove:
                    print(f"   [SYNC] Removing ghost file: {filename}")
                    db.delete_file(filename)
                
            except Exception as e:
                print(f"⚠️ Sync Error: {e}")
            
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

    # --- OPEN FILE ---
    def open(self, path, flags):
        full_path = self._full_path(path)
        filename = os.path.basename(path)

        # Security Check (Case-Insensitive)
        is_locked = self.lock_cache.get(filename.lower(), False)
        if is_locked:
            print(f"🔒 [BLOCKED OPEN] {filename}")
            raise FuseOSError(errno.EACCES)
        
        # Async Stat Update
        if self._is_valid_file(filename):
            threading.Thread(target=db.update_last_accessed, args=(filename,)).start()

        # Windows Flags Fix
        access_flags = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        final_flags = flags & access_flags
        final_flags |= os.O_BINARY

        return os.open(full_path, final_flags)

    # --- FILE MODIFICATIONS ---
    def create(self, path, mode, fi=None):
        full_path = self._full_path(path)
        filename = os.path.basename(path)
        self.lock_cache[filename] = False
        if self._is_valid_file(filename):
            threading.Thread(target=db.insert_file, args=(filename,)).start()
        return os.open(full_path, os.O_WRONLY | os.O_CREAT | os.O_BINARY, mode)

    def unlink(self, path):
        full_path = self._full_path(path)
        filename = os.path.basename(path)
        os.unlink(full_path)
        if self._is_valid_file(filename):
            threading.Thread(target=db.delete_file, args=(filename,)).start()
        if filename in self.lock_cache:
            del self.lock_cache[filename]

    def rename(self, old, new):
        full_old = self._full_path(old)
        full_new = self._full_path(new)
        os.rename(full_old, full_new)
        old_name = os.path.basename(old)
        new_name = os.path.basename(new)
        if self._is_valid_file(old_name) and self._is_valid_file(new_name):
            threading.Thread(target=db.rename_file, args=(old_name, new_name)).start()

    # --- STANDARD IO ---
    def read(self, path, length, offset, fh):
        # Security Check (Enforce on READ)
        filename = os.path.basename(path)
        if self.lock_cache.get(filename.lower(), False):
            print(f"🔒 [BLOCKED READ] {filename}")
            raise FuseOSError(errno.EACCES)

        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    def write(self, path, buf, offset, fh):
        # Security Check (Enforce on WRITE)
        filename = os.path.basename(path)
        if self.lock_cache.get(filename.lower(), False):
            print(f"🔒 [BLOCKED WRITE] {filename}")
            raise FuseOSError(errno.EACCES)

        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    def release(self, path, fh):
        return os.close(fh)
    
    def flush(self, path, fh):
        return os.fsync(fh)
    
    # --- WINDOWS FIXES ---
    def utimens(self, path, times=None):
        return os.utime(self._full_path(path), times)
    
    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        with open(full_path, 'r+') as f:
            f.truncate(length)
            
    def chmod(self, path, mode):
        return os.chmod(self._full_path(path), mode)
    
    def chown(self, path, uid, gid):
        pass

if __name__ == '__main__':
    if not os.path.exists(SOURCE_DIR):
        os.makedirs(SOURCE_DIR)
    
    print(f"🚀 Gatekeeper Active on {MOUNT_POINT}")
    try:
        FUSE(Gatekeeper(SOURCE_DIR), MOUNT_POINT, foreground=True, nothreads=False)
    except Exception as e:
        print(f"Error: {e}")
