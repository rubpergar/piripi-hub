import logging
import hashlib
import os
from dotenv import load_dotenv
from app.modules.fakenodo.repositories import DepositionRepo
from app.modules.fakenodo.models import Deposition
from app.modules.dataset.models import DataSet
from app.modules.featuremodel.models import FeatureModel
from core.configuration.configuration import uploads_folder_name
from core.services.BaseService import BaseService
from flask_login import current_user

logger = logging.getLogger(__name__)
load_dotenv()


class FakenodoService(BaseService):
    def __init__(self):
        self.deposition_repository = DepositionRepo()

    def create_new_deposition(self, dataset: DataSet) -> dict:
        ds_meta_data = dataset.ds_meta_data
        logger.info("Dataset sending to Fakenodo")
        logger.info(f"Publication type: {ds_meta_data.publication_type.value}")
        metadataJSON = {
            "title": ds_meta_data.title,
            "upload_type": (
                "dataset"
                if ds_meta_data.publication_type.value == "none"
                else "publication"
            ),
            "publication_type": (
                str(ds_meta_data.publication_type.value)
                if ds_meta_data.publication_type
                else None
            ),
            "description": ds_meta_data.description,
            "creators": [
                {
                    "name": author.name,
                    **(
                        {"affiliation": author.affiliation}
                        if author.affiliation
                        else {}
                    ),
                    **({"orcid": author.orcid} if author.orcid else {}),
                }
                for author in ds_meta_data.authors
            ],
            "keywords": (
                ["uvlhub"]
                if not ds_meta_data.tags
                else ds_meta_data.tags.split(", ") + ["uvlhub"]
            ),
            "access_right": "open",
            "license": "CC-BY-4.0",
        }
        try:
            deposition = self.deposition_repository.create_new_deposition(
                dep_metadata=metadataJSON, doi=ds_meta_data.publication_doi
            )
            return {
                "id": deposition.id,
                "metadata": metadataJSON,
                "message": "Deposition succesfully created in Fakenodo",
            }
        except Exception as error400:
            raise Exception(
                f"Failed to create deposition in Fakenodo with error: {str(error400)}"
            )

    def upload_file(
        self,
        dataset: DataSet,
        deposition_id: int,
        feature_model: FeatureModel,
        user=None,
    ):
        uvl_filename = feature_model.fm_meta_data.uvl_filename
        user_id = current_user.id if user is None else user.id
        file_path = os.path.join(
            uploads_folder_name(),
            f"user_{str(user_id)}",
            f"dataset_{dataset.id}/",
            uvl_filename,
        )
        request = {
            "id": deposition_id,
            "file": uvl_filename,
            "fileSize": os.path.getsize(file_path),
            "checksum": self.checksum(file_path),
            "message": f"File Uploaded to deposition with id {deposition_id}",
        }
        return request

    def publish_deposition(self, deposition_id: int) -> dict:
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
                "message": "Deposition published successfully in fakenodo.",
            }
            return response
        except Exception as error:
            raise Exception(f"Failed to publish deposition with errors: {str(error)}")

    def get_deposition(self, deposition_id: int) -> dict:
        deposition = Deposition.query.get(deposition_id)
        if not deposition:
            raise Exception("Deposition not found")
        response = {
            "id": deposition.id,
            "doi": deposition.doi,
            "metadata": deposition.dep_metadata,
            "status": deposition.status,
            "message": "Deposition succesfully get from Fakenodo.",
        }
        return response

    def get_doi(self, deposition_id: int) -> str:
        return self.get_deposition(deposition_id).get("doi")

    def checksum(self, fileName):
        try:
            with open(fileName, "rb") as file:
                file_content = file.read()
                res = hashlib.sha256(file_content).hexdigest()
            return res
        except FileNotFoundError:
            raise Exception(f"File {fileName} not found for checksum calculation")
        except Exception as e:
            raise Exception(f"Error calculating checksum for file {fileName}: {str(e)}")
