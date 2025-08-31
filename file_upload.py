import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
import mimetypes

class FileUploadHandler:
    def __init__(self, upload_folder='uploads'):
        self.upload_folder = upload_folder
        self.allowed_extensions = {
            'images': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'svg'},
            'documents': {'pdf', 'doc', 'docx', 'txt', 'rtf'},
            'design': {'ai', 'eps', 'psd', 'indd', 'cdr'},
            'vector': {'svg', 'eps', 'ai', 'pdf'}
        }
        self.max_file_size = 50 * 1024 * 1024  # 50MB limit
        
        # Create upload directories
        self.ensure_upload_dirs()
    
    def ensure_upload_dirs(self):
        """Create necessary upload directories"""
        base_dir = os.path.join('static', self.upload_folder)
        directories = ['quotes', 'orders', 'customers', 'temp']
        
        for directory in directories:
            dir_path = os.path.join(base_dir, directory)
            os.makedirs(dir_path, exist_ok=True)
    
    def allowed_file(self, filename, category='images'):
        """Check if file extension is allowed"""
        if '.' not in filename:
            return False
        
        extension = filename.rsplit('.', 1)[1].lower()
        return extension in self.allowed_extensions.get(category, set())
    
    def get_file_category(self, filename):
        """Determine file category based on extension"""
        if not '.' in filename:
            return 'unknown'
        
        extension = filename.rsplit('.', 1)[1].lower()
        
        for category, extensions in self.allowed_extensions.items():
            if extension in extensions:
                return category
        
        return 'unknown'
    
    def generate_unique_filename(self, filename):
        """Generate a unique filename while preserving extension"""
        if '.' in filename:
            name, ext = filename.rsplit('.', 1)
            unique_name = f"{uuid.uuid4().hex[:8]}_{secure_filename(name)}.{ext}"
        else:
            unique_name = f"{uuid.uuid4().hex[:8]}_{secure_filename(filename)}"
        
        return unique_name
    
    def save_quote_file(self, file, quote_id, description=""):
        """Save a file associated with a quote"""
        if not file or not file.filename:
            return None, "No file selected"
        
        if not self.allowed_file(file.filename, 'images') and \
           not self.allowed_file(file.filename, 'documents') and \
           not self.allowed_file(file.filename, 'design'):
            return None, "File type not allowed"
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > self.max_file_size:
            return None, f"File too large. Maximum size is {self.max_file_size // (1024*1024)}MB"
        
        try:
            # Generate unique filename
            unique_filename = self.generate_unique_filename(file.filename)
            file_path = os.path.join('static', self.upload_folder, 'quotes', unique_filename)
            
            # Save file
            file.save(file_path)
            
            # Get file info
            file_category = self.get_file_category(file.filename)
            mime_type = mimetypes.guess_type(file.filename)[0] or 'application/octet-stream'
            
            # Create database record
            from app import QuoteFile, db
            
            quote_file = QuoteFile(
                quote_id=quote_id,
                filename=unique_filename,
                original_filename=file.filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_category,
                description=description
            )
            
            db.session.add(quote_file)
            db.session.commit()
            
            return quote_file, "File uploaded successfully"
            
        except Exception as e:
            return None, f"Error uploading file: {str(e)}"
    
    def get_file_url(self, quote_file):
        """Get URL for serving a quote file"""
        return f"/static/{self.upload_folder}/quotes/{quote_file.filename}"
    
    def delete_file(self, quote_file):
        """Delete a file from storage and database"""
        try:
            # Delete physical file
            if os.path.exists(quote_file.file_path):
                os.remove(quote_file.file_path)
            
            # Delete database record
            from app import db
            db.session.delete(quote_file)
            db.session.commit()
            
            return True, "File deleted successfully"
        except Exception as e:
            return False, f"Error deleting file: {str(e)}"
    
    def get_file_icon(self, file_type):
        """Get appropriate icon for file type"""
        icons = {
            'images': 'fa-image',
            'documents': 'fa-file-text',
            'design': 'fa-paint-brush',
            'vector': 'fa-vector-square',
            'unknown': 'fa-file'
        }
        return icons.get(file_type, 'fa-file')
    
    def format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        import math
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"