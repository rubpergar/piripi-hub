import logging
import os
import requests

from app.modules.dataset.models import DataSet
from app.modules.featuremodel.models import FeatureModel
from app.modules.fakenodo.repositories import FakenodoRepository

from core.configuration.configuration import uploads_folder_name
from dotenv import load_dotenv
from flask import jsonify, Response
from flask_login import current_user


from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)

load_dotenv()


class FakenodoService(BaseService):

    def get_fakenodo_url(self):

        FLASK_ENV = os.getenv("FLASK_ENV", "development")
        FAKENODO_API_URL = ""

        if FLASK_ENV == "development":
            FAKENODO_API_URL = os.getenv(
                "FAKENODO_API_URL", "https://sandbox.fakenodo.org/api/deposit/depositions"
            )
        elif FLASK_ENV == "production":
            FAKENODO_API_URL = os.getenv(
                "FAKENODO_API_URL", "https://fakenodo.org/api/deposit/depositions"
            )
        else:
            FAKENODO_API_URL = os.getenv(
                "FAKENODO_API_URL", "https://sandbox.fakenodo.org/api/deposit/depositions"
            )

        return FAKENODO_API_URL

    def get_fakenodo_access_token(self):
        return os.getenv("FAKENODO_ACCESS_TOKEN")

    def __init__(self):
        super().__init__(FakenodoRepository())
        self.FAKENODO_ACCESS_TOKEN = self.get_fakenodo_access_token()
        self.FAKENODO_API_URL = self.get_fakenodo_url()
        self.headers = {"Content-Type": "application/json"}
        self.params = {"access_token": self.FAKENODO_ACCESS_TOKEN}

    def test_connection(self) -> bool:
        """
        Test the connection with Fakenodo.

        Returns:
            bool: True if the connection is successful, False otherwise.
        """
        response = requests.get(
            self.FAKENODO_API_URL, params=self.params, headers=self.headers
        )
        return response.status_code == 200

    def test_full_connection(self) -> Response:
        """
        Test the connection with Fakenodo by creating a deposition, uploading an empty test file, and deleting the
        deposition.

        Returns:
            bool: True if the connection, upload, and deletion are successful, False otherwise.
        """

        success = True

        # Create a test file
        working_dir = os.getenv("WORKING_DIR", "")
        file_path = os.path.join(working_dir, "test_file.txt")
        with open(file_path, "w") as f:
            f.write("This is a test file with some content.")

        messages = []  # List to store messages

        # Step 1: Create a deposition on Fakenodo
        data = {
            "metadata": {
                "title": "Test Deposition",
                "upload_type": "dataset",
                "description": "This is a test deposition created via Fakenodo API",
                "creators": [{"name": "John Doe"}],
            }
        }

        response = requests.post(
            self.FAKENODO_API_URL, json=data, params=self.params, headers=self.headers
        )

        if response.status_code != 201:
            return jsonify(
                {
                    "success": False,
                    "messages": f"Failed to create test deposition on Fakenodo. Response code: {response.status_code}",
                }
            )

        deposition_id = response.json()["id"]

        # Step 2: Upload an empty file to the deposition
        data = {"name": "test_file.txt"}
        files = {"file": open(file_path, "rb")}
        publish_url = f"{self.FAKENODO_API_URL}/{deposition_id}/files"
        response = requests.post(
            publish_url, params=self.params, data=data, files=files
        )
        files["file"].close()  # Close the file after uploading

        logger.info(f"Publish URL: {publish_url}")
        logger.info(f"Params: {self.params}")
        logger.info(f"Data: {data}")
        logger.info(f"Files: {files}")
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Content: {response.content}")

        if response.status_code != 201:
            messages.append(
                f"Failed to upload test file to Fakenodo. Response code: {response.status_code}"
            )
            success = False

        # Step 3: Delete the deposition
        response = requests.delete(
            f"{self.FAKENODO_API_URL}/{deposition_id}", params=self.params
        )

        if os.path.exists(file_path):
            os.remove(file_path)

        return jsonify({"success": success, "messages": messages})

    def get_all_depositions(self) -> dict:
        """
        Get all depositions from Fakenodo.

        Returns:
            dict: The response in JSON format with the depositions.
        """
        response = requests.get(
            self.FAKENODO_API_URL, params=self.params, headers=self.headers
        )
        if response.status_code != 200:
            raise Exception("Failed to get depositions")
        return response.json()

    def get_doi(self, deposition_id: int) -> str:
        """
        Get the DOI of a deposition from Fakenodo.

        Args:
            deposition_id (int): The ID of the deposition in Fakenodo.

        Returns:
            str: The DOI of the deposition.
        """
        return self.get_deposition(deposition_id).get("doi")
