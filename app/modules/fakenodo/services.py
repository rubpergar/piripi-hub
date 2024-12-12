import logging
import hashlib
import os

from dotenv import load_dotenv
from app.modules.fakenodo.repositories import DepositionRepo
from app.modules.fakenodo.models import Deposition
from app.modules.dataset.models import DataSet, DSMetaData
from app.modules.featuremodel.models import FeatureModel

from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService
from flask_login import current_user

logger = logging.getLogger(__name__)

load_dotenv()


class FakenodoService(BaseService):
    def __init__(self):
        self.deposition_repository = DepositionRepo()

    def create_new_deposition(self, ds_meta_data: DSMetaData) -> dict:
        """
        Create a new deposition in Fakenodo

        Args:
            dataset (Dataset): The dataset contain ing the necessary metadata

        Returns:
            dict: JSON format with the details of the deposition
        """

        logger.info("Dataset sending to Fakenodo")
        logger.info(f"Publication type: {ds_meta_data.publication_type.value}")

        metadataJSON = {
            "title": ds_meta_data.title,
            "upload_type": "dataset" if ds_meta_data.publication_type.value == "none" else "publication",
            "publication_type": (
                ds_meta_data.publication_type.value
                if ds_meta_data.publication_type.value != "none"
                else None
            ),
            "description": ds_meta_data.description,
            "creators": [
                {
                    "name": author.name,
                    **({"affiliation": author.affiliation} if author.affiliation else {}),
                    **({"orcid": author.orcid} if author.orcid else {}),
                }
                for author in ds_meta_data.authors
            ],
            "keywords": (
                ["uvlhub"] if not ds_meta_data.tags else ds_meta_data.tags.split(", ") + ["uvlhub"]
            ),
            "access_right": "open",
            "license": "CC-BY-4.0",
        }

        try:
            deposition = self.deposition_repository.create_new_deposition(dep_metadata=metadataJSON)

            return {
                "id": deposition.id,
                "metadata": metadataJSON,
                "message": "Deposition succesfully created in Fakenodo"
            }
        except Exception as error400:
            raise Exception(f"Failed to create deposition in Fakenodo with error: {str(error400)}")

    def upload_file(self, dataset: DataSet, deposition_id: int, feature_model: FeatureModel, user=None):
        """
        Upload a file to a deposition in Fakenodo.

        Args:
            deposition_id (int): The ID of the deposition in Fakenodo.
            feature_model (FeatureModel): The FeatureModel object representing the feature model.
            user (FeatureModel): The User object representing the file owner.

        Returns:
            dict: The response in JSON format with the details of the uploaded file.
        """

        uvl_filename = feature_model.fm_meta_data.uvl_filename
        user_id = current_user.id if user is None else user.id
        file_path = os.path.join(uploads_folder_name(), f"user_{str(user_id)}", f"dataset_{dataset.id}/", uvl_filename)

        request = {
            "id": deposition_id,
            "file": uvl_filename,
            "fileSize": os.path.getsize(file_path),
            "checksum": checksum(file_path),
            "message": f"File Uploaded to deposition with id {deposition_id}"
        }

        return request

    def publish_deposition(self, deposition_id: int) -> dict:
        """
        Publish a deposition in Fakenodo.

        Args:
            deposition_id (int): The ID of the deposition in Fakenodo.

        Returns:
            dict: The response in JSON format with the details of the published deposition.
        """

        deposition = Deposition.query.get(deposition_id)
        if not deposition:
            raise Exception("Error 404: Deposition not found")

        try:
            deposition.doi = f"fakenodo.doi.{deposition_id}"
            deposition.status = "published"
            self.deposition_repository.update(deposition)

            response = {
                "id": deposition_id,
                "status": "published",
                "conceptdoi": f"fakenodo.doi.{deposition_id}",
                "message": "Deposition published successfully in fakenodo."
            }
            return response

        except Exception as error:
            raise Exception(f"Failed to publish deposition with errors: {str(error)}")

    def get_deposition(self, deposition_id: int) -> dict:
        """
        Get a deposition from Fakenodo.

        Args:
            deposition_id (int): The ID of the deposition in Fakenodo.

        Returns:
            dict: The response in JSON format with the details of the deposition.
        """
        deposition = Deposition.query.get(deposition_id)
        if not deposition:
            raise Exception("Deposition not found")

        response = {
            "id": deposition.id,
            "doi": deposition.doi,
            "metadata": deposition.dep_metadata,
            "status": deposition.status,
            "message": "Deposition succesfully get from Fakenodo."
        }
        return response

    def get_doi(self, deposition_id: int) -> str:
        """
        Get the DOI of a deposition from Fakenodo.

        Args:
            deposition_id (int): The ID of the deposition in Fakenodo.

        Returns:
            str: The DOI of the deposition.
        """
        return self.get_deposition(deposition_id).get("doi")


def checksum(fileName):
    try:
        with open(fileName, "rb") as file:
            file_content = file.read()
            res = hashlib.sha256(file_content).hexdigest()
        return res
    except FileNotFoundError:
        raise Exception(f"File {fileName} not found for checksum calculation")
    except Exception as e:
        raise Exception(f"Error calculating checksum for file {fileName}: {str(e)}")