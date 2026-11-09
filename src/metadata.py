from pathlib import Path
import yaml


class MetadataLoader:

    def __init__(self, metadata_folder):
        self.metadata_folder = Path(metadata_folder)

    def load_structure(self, record_type):

        file = self.metadata_folder / f"{record_type}.yaml"

        if not file.exists():
            raise FileNotFoundError(file)

        with open(file, encoding="utf-8") as f:
            return yaml.safe_load(f)
