from pathlib import Path
from uuid import uuid4

from app.config import settings


class Storage:

    def __init__(self):

        self.directory = Path(settings.IMAGE_DIR)

        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def save_bytes(
        self,
        data: bytes,
        extension: str,
    ) -> str:
        clean_extension = extension.lstrip(".").lower() or "bin"
        filename = f"{uuid4()}.{clean_extension}"

        filepath = self.directory / filename

        filepath.write_bytes(data)

        return filename


storage = Storage()
