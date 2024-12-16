from unittest.mock import MagicMock
import pytest
from app.modules.explore.services import ExploreService
from app.modules.explore.repositories import ExploreRepository


@pytest.fixture
def explore_service():
    service = ExploreService()

    service.repository = MagicMock(ExploreRepository)

    return service


def test_filter_success(explore_service):
    explore_service.repository.filter.return_value = [
        {"title": "Post 1", "tags": ["software", "innovación"]},
        {"title": "Post 2", "tags": ["tecnología", "innovación"]},
    ]

    result = explore_service.filter(
        query="tecnología",
        sorting="newest",
        publication_type="any",
        tags=["software", "innovación"],
        number_of_features="5",
        number_of_models="3",
    )

    explore_service.repository.filter.assert_called_with(
        "tecnología", "newest", "any", ["software", "innovación"], "5", "3", **{}
    )

    assert len(result) == 2
    assert result[0]["title"] == "Post 1"
    assert result[1]["title"] == "Post 2"


def test_filter_no_results(explore_service):
    explore_service.repository.filter.return_value = []

    result = explore_service.filter(query="nonexistent", tags=["nonexistenttag"])

    assert result == []
