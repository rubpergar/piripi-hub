import pytest

from datetime import datetime
from app import db
from app.modules.auth.models import User
from app.modules.profile.models import UserProfile
from app.modules.dataset.models import DSMetrics, DSMetaData, DataSet, DSDownloadRecord, DSViewRecord, RateDatasets
from app.modules.conftest import login


@pytest.fixture(scope="module")
def test_client(test_client):
    """
    Extends the test_client fixture to add additional specific data for module testing.
    """

    with test_client.application.app_context():
        # Crear un usuario de prueba
        user_test = User(email='user@example.com', password='test1234')
        db.session.add(user_test)
        db.session.commit()

        # Crear perfil de usuario
        profile = UserProfile(user_id=user_test.id, name="Name", surname="Surname")
        db.session.add(profile)
        db.session.commit()

        # Crear métricas para el dataset
        ds_metrics = DSMetrics(number_of_models="5", number_of_features="50")
        db.session.add(ds_metrics)
        db.session.commit()

        # Crear metadatos del dataset
        ds_meta_data = DSMetaData(
            deposition_id=12345,
            title="Sample Dataset",
            description="This is a sample dataset for testing.",
            publication_type="DATA_MANAGEMENT_PLAN",
            publication_doi="10.1234/test_doi",
            dataset_doi="10.5678/test_dataset_doi",
            tags="test,sample,dataset",
            ds_metrics_id=ds_metrics.id
        )
        db.session.add(ds_meta_data)
        db.session.commit()

        # Crear un dataset asociado al usuario
        dataset = DataSet(
            user_id=user_test.id,
            ds_meta_data_id=ds_meta_data.id,
            created_at=datetime.utcnow()
        )
        db.session.add(dataset)
        db.session.commit()

        # Crear registro de descarga del dataset
        ds_download_record = DSDownloadRecord(
            user_id=user_test.id,
            dataset_id=dataset.id,
            download_date=datetime.utcnow(),
            download_cookie="123e4567-e89b-12d3-a456-426614174000"
        )
        db.session.add(ds_download_record)
        db.session.commit()

        # Crear registro de visualización del dataset
        ds_view_record = DSViewRecord(
            user_id=user_test.id,
            dataset_id=dataset.id,
            view_date=datetime.utcnow(),
            view_cookie="223e4567-e89b-12d3-a456-426614174001"
        )
        db.session.add(ds_view_record)
        db.session.commit()

        # Crear valoración para el dataset
        rate_datasets = RateDatasets(
            rate=5,
            comment="Excellent dataset!",
            dataset_id=dataset.id,
            user_id=user_test.id
        )
        db.session.add(rate_datasets)
        db.session.commit()

    yield test_client


def test_get_viewRate(test_client):
    response = test_client.get("/rate/1")
    assert response.status_code == 200
    assert 'Excellent dataset!' in response.get_data(as_text=True)


def test_create_rate(test_client):
    login(test_client, "user@example.com", "test1234")
    response = test_client.post(
        "/ratedataset/create/1",
        data={
            'rate': '5',
            'comment': 'Testing',
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    responsito = test_client.get("/rate/1")
    assert 'Testing' in responsito.get_data(as_text=True)


def test_edit_rate(test_client):
    login(test_client, "user@example.com", "test1234")
    response = test_client.post(
        '/ratedataset/edit/1/1',
        data={
            'rate': '10',
            'comment': 'EditPrueba',
        },
        follow_redirects=True
    )

    assert response.status_code == 200
    responsito = test_client.get("/rate/1")
    assert 'EditPrueba' in responsito.get_data(as_text=True)


def test_delete_rate(test_client):
    login(test_client, "user@example.com", "test1234")
    response = test_client.post(
        '/ratedataset/delete/1/1',
        follow_redirects=True
    )

    assert response.status_code == 200
    responsito = test_client.get("/rate/1")
    assert 'EditPrueba' not in responsito.get_data(as_text=True)
