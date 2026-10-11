from app.api.exceptions.global_exception_handler import MaximumFileSizeException
import zipfile
from uuid import uuid4
from app.api.exceptions.global_exception_handler import InvalidFileException
from fastapi import UploadFile, status
from pathlib import Path

UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 1000 * 1024 * 1024  
ALLOWED_EXTENSIONS = {".kml", ".zip"}

class UploadFileService:
    def __init__(self):
        pass

    def validate_file_type(self, file: UploadFile):
        if not file.filename:
            raise InvalidFileException("Filename is required.")
        extension = Path(file.filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise InvalidFileException("Only KML files and ZIP Shapefiles are supported.")
        return extension

    async def save_file(self, file: UploadFile, extension: str):
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        file_id = str(uuid4())
        saved_path = UPLOAD_DIR / f"{file_id}{extension}"
        size = 0
        try:
            size = await self._write_file_by_chunk(file, saved_path)
            if size == 0:
                raise InvalidFileException("Uploaded file is empty.", status.HTTP_404_NOT_FOUND)
            self._handle_zip_file(extension, saved_path)

        except Exception:
            saved_path.unlink(missing_ok=True)
            raise

        finally:
            await file.close()
        return file_id, saved_path, size

    def remove_file(self, file_path: Path):
        file_path.unlink(missing_ok=True)

    def _handle_zip_file(self, extension: str, saved_path: str):
        if extension == ".zip":
            if not zipfile.is_zipfile(saved_path):
                raise InvalidFileException("Invalid ZIP archive.")

            with zipfile.ZipFile(saved_path) as archive:
                shp_files = [
                    name for name in archive.namelist()
                    if Path(name).suffix.lower() == ".shp"
                    and not name.startswith("/")
                    and ".." not in Path(name).parts
                ]

                if not shp_files:
                    raise InvalidFileException("ZIP archive does not contain a Shapefile.", status.HTTP_404_NOT_FOUND)

    async def _write_file_by_chunk(self, file: UploadFile, saved_path: str):
        size = 0
        with saved_path.open("wb") as destination:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_FILE_SIZE:
                    raise MaximumFileSizeException("File exceeds the 50 MB limit.")
                destination.write(chunk)
        
        return size