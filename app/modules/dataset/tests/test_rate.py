import pytest

from datetime import datetime
from app import db
from app.modules.auth.models import User
from app.modules.profile.models import UserProfile
from app.modules.dataset.models import DSMetrics, DSMetaData, DataSet, RateDatasets
from app.modules.conftest import login
from flask_login import current_user, logout_user
from app.modules.dataset.services import RateDataSetService

rateDataset_service = RateDataSetService()


@pytest.fixture(scope="module")
def test_client(test_client):
    with test_client.application.app_context():
        # Crear usuarios de prueba
        user_test = User(email="user@example.com", password="test1234")
        db.session.add(user_test)
        db.session.commit()

        user_test1 = User(email="user1@example.com", password="test1234")
        db.session.add(user_test1)
        db.session.commit()

        # Crear perfil de usuario
        profile = UserProfile(user_id=user_test.id, name="Name", surname="Surname")
        db.session.add(profile)
        db.session.commit()

        profile = UserProfile(user_id=user_test1.id, name="Name1", surname="Surname1")
        db.session.add(profile)
        db.session.commit()

        # Crear dataset asociado a user_test
        ds_metrics = DSMetrics(number_of_models="5", number_of_features="50")
        db.session.add(ds_metrics)
        db.session.commit()

        ds_meta_data = DSMetaData(
            deposition_id=12345,
            title="Sample Dataset",
            description="This is a sample dataset for testing.",
            publication_type="DATA_MANAGEMENT_PLAN",
            publication_doi="10.1234/test_doi",
            dataset_doi="10.5678/test_dataset_doi",
            tags="test,sample,dataset",
            ds_metrics_id=ds_metrics.id,
        )
        db.session.add(ds_meta_data)
        db.session.commit()

        dataset = DataSet(
            user_id=user_test.id,  # Asegúrate de que el dataset esté asociado al usuario test
            ds_meta_data_id=ds_meta_data.id,
            created_at=datetime.utcnow(),
        )
        db.session.add(dataset)
        db.session.commit()

        # Crear valoración para el dataset y asignarla a user_test (el creador)
        rate_datasets = RateDatasets(
            rate=5,
            comment="Excellent dataset!",
            dataset_id=dataset.id,
            user_id=user_test.id,  # Asocia la valoración a user_test
        )
        db.session.add(rate_datasets)
        db.session.commit()

    yield test_client


def test_get_viewRate(test_client):
    response = test_client.get("/rate/1")
    assert response.status_code == 200
    assert "Excellent dataset!" in response.get_data(as_text=True)


def test_create_rate(test_client):
    login(test_client, "user@example.com", "test1234")
    response = test_client.post(
        "/ratedataset/create/1",
        data={
            "rate": "5",
            "comment": "Testing",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    responsito = test_client.get("/rate/1")
    assert "Testing" in responsito.get_data(as_text=True)


def test_edit_rate(test_client):
    login(test_client, "user@example.com", "test1234")
    response = test_client.post(
        "/ratedataset/edit/1/1",
        data={
            "rate": "10",
            "comment": "EditPrueba",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    responsito = test_client.get("/rate/1")
    assert "EditPrueba" in responsito.get_data(as_text=True)


def test_edit_rate_not_authorized(test_client):
    logout_user()
    login(test_client, "user1@example.com", "test1234")

    assert current_user.email == "user1@example.com"

    rate = rateDataset_service.get_or_404(1)
    assert rate.user_id != current_user.id

    response = test_client.post(
        "/ratedataset/edit/1/1",
        data={
            "rate": "5",
            "comment": "Este es un comentario editado",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200

    # Verifica que el comentario no fue editado
    responsito = test_client.get("/rate/1")
    assert "Este es un comentario editado" not in responsito.get_data(as_text=True)
    assert "EditPrueba" in responsito.get_data(as_text=True)


def test_delete_rate_not_authorized(test_client):
    logout_user()
    login(test_client, "user1@example.com", "test1234")
    response = test_client.post("/ratedataset/delete/1/1", follow_redirects=True)

    assert response.status_code == 200
    responsito = test_client.get("/rate/1")
    assert "EditPrueba" in responsito.get_data(as_text=True)


def test_delete_rate(test_client):
    logout_user()
    login(test_client, "user@example.com", "test1234")
    response = test_client.post("/ratedataset/delete/1/1", follow_redirects=True)

    assert response.status_code == 200
    responsito = test_client.get("/rate/1")
    assert "EditPrueba" not in responsito.get_data(as_text=True)
