import os
import sys
import errno
from fuse import FUSE, FuseOSError, Operations

class Gatekeeper(Operations):
    def __init__(self, root):
        self.root = root

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join(self.root, partial)
        return path

    # --- 1. ATTRIBUTES ---
    def getattr(self, path, fh=None):
        full_path = self._full_path(path)
        st = os.lstat(full_path)
        return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
                     'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

    # --- 2. READ DIRECTORY ---
    def readdir(self, path, fh):
        full_path = self._full_path(path)
        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(os.listdir(full_path))
        for r in dirents:
            yield r

    # --- 3. OPEN FILE (THE FIX: FLAG SANITIZATION) ---
    def open(self, path, flags):
        full_path = self._full_path(path)
        filename = os.path.basename(path)

        # SECURITY CHECK
        if "secret" in filename.lower():
            print(f"🛑 [BLOCKED] User tried to open: {filename}")
            raise FuseOSError(errno.EACCES)
        
        print(f"✅ [ALLOWED] Accessing: {filename}")

        # === THE FIX IS HERE ===
        # Windows sends complex flags that confuse Python. 
        # We manually strip them and force simple READ/WRITE + BINARY mode.
        
        access_flags = os.O_RDONLY | os.O_WRONLY | os.O_RDWR
        
        # Keep only the access mode (Read/Write) from the original request
        final_flags = flags & access_flags
        
        # FORCE BINARY MODE (Critical for Windows Notepad)
        final_flags |= os.O_BINARY

        return os.open(full_path, final_flags)

    # --- 4. READ ---
    def read(self, path, length, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.read(fh, length)

    # --- 5. WRITE ---
    def write(self, path, buf, offset, fh):
        os.lseek(fh, offset, os.SEEK_SET)
        return os.write(fh, buf)

    # --- 6. CREATE ---
    def create(self, path, mode, fi=None):
        full_path = self._full_path(path)
        return os.open(full_path, os.O_WRONLY | os.O_CREAT | os.O_BINARY, mode)

    # --- 7. RELEASE ---
    def release(self, path, fh):
        return os.close(fh)
    
    # --- 8. FLUSH ---
    def flush(self, path, fh):
        return os.fsync(fh)

if __name__ == '__main__':
    # CONFIGURATION
    SOURCE_DIR = "my_hidden_data"
    MOUNT_POINT = "S:" 

    if not os.path.exists(SOURCE_DIR):
        os.makedirs(SOURCE_DIR)

    print(f"🛡️  Gatekeeper Active on {MOUNT_POINT}")
    
    try:
        FUSE(Gatekeeper(SOURCE_DIR), MOUNT_POINT, foreground=True, nothreads=True, fsname="Gatekeeper_Secure")
    except Exception as e:
        print(f"Error: {e}")