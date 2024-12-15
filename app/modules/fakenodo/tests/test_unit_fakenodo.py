import pytest
from unittest.mock import patch, MagicMock
from app.modules.fakenodo.services import FakenodoService
from app.modules.fakenodo.models import Deposition

@pytest.fixture
def mock_dataset():
    mock_dataset = MagicMock()
    mock_dataset.ds_meta_data.title = "Test Dataset"
    mock_dataset.ds_meta_data.description = "A dataset for testing"
    mock_dataset.ds_meta_data.publication_type.value = "none" 
    mock_dataset.ds_meta_data.authors = [
        MagicMock(name="author", affiliation="University", orcid="0000-0000-0000-0000")
    ]
    mock_dataset.ds_meta_data.tags = "science, research"
    mock_dataset.ds_meta_data.publication_doi = "10.1234/test-doi"
    return mock_dataset

def test_create_new_deposition_failure(mock_dataset):
    mock_deposition_repo = MagicMock()
    mock_deposition_repo.create_new_deposition.side_effect = Exception("Database error")

    fakenodo_service = FakenodoService()
    fakenodo_service.deposition_repository = mock_deposition_repo

    with pytest.raises(Exception, match="Failed to create deposition in Fakenodo with error: Database error"):
        fakenodo_service.create_new_deposition(mock_dataset)


@patch.object(FakenodoService, "get_deposition")
def test_get_doi_success(mock_get_deposition):
    mock_get_deposition.return_value = {"doi": "10.1234/fakenodo.5678"}

    fakenodo_service = FakenodoService()

    deposition_id = 1
    doi = fakenodo_service.get_doi(deposition_id)

    mock_get_deposition.assert_called_once_with(deposition_id)
    assert doi == "10.1234/fakenodo.5678"

@patch.object(FakenodoService, "get_deposition")
def test_get_doi_not_found(mock_get_deposition):
    mock_get_deposition.side_effect = Exception("Deposition not found")

    fakenodo_service = FakenodoService()

    deposition_id = 1
    with pytest.raises(Exception, match="Deposition not found"):
        fakenodo_service.get_doi(deposition_id)

    mock_get_deposition.assert_called_once_with(deposition_id)







