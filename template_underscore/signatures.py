import json
import os
from datetime import datetime

class Signatures:
 
    ########################################################################################
    def __init__(self, file_path='signatures.json'):
        if file_path != 'signatures.json': file_path = f"signatures-{file_path}"
        self.file_path = file_path
        self.signatures = {}
        self.load()

    ########################################################################################
    def load(self):
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    self.signatures = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.signatures = {}
        else:
            self.signatures = {}

    ########################################################################################
    def save(self):
        try:
            with open(self.file_path, 'w') as f:
                json.dump(self.signatures, f, indent=2)
        except IOError as e:
            print(f"Error saving file: {e}")

    ########################################################################################
    def search(self, document_id):
        """Return the signature (update date) for a given document ID, or None if not found."""
        return self.signatures.get(document_id)

    ########################################################################################
    def update (self, document_id: str, update_date: datetime = None):
        self.signatures[document_id] = update_date or self._current_date()
        self.save()

    ########################################################################################
    def remove(self, document_id):
        """Remove a signature by document ID."""
        if document_id in self.signatures:
            del self.signatures[document_id]

    ########################################################################################
    def _current_date(self):
        """Get the current date in ISO 8601 format."""
        return datetime.utcnow().isoformat()


# Example usage
if __name__ == "__main__":
    print ("Cannot be executed. Import into a script.")
    quit()
    