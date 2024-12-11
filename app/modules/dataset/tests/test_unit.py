import shutil
import pytest
import os
from app import db
from app.modules.auth.models import User
from app.modules.featuremodel.models import FeatureModel
from app.modules.hubfile.models import Hubfile
from app.modules.dataset.models import (
    DSMetaData,
    PublicationType,
    DataSet,
)
from app.modules.dataset.routes import to_glencoe, to_splot, to_cnf


@pytest.fixture(scope="module")
def test_client(test_client):

    with test_client.application.app_context():
        user_test = create_user(email="user_test@example.com", password="password123")
        dataset_test = create_dataset(user_id=user_test.id)

        os.makedirs(
            f"uploads/user_{user_test.id}/dataset_{dataset_test.id}", exist_ok=True
        )
        with open(
            f"uploads/user_{user_test.id}/dataset_{dataset_test.id}/file100.uvl",
            "w",
        ) as f:
            f.write(
                'features\n    Chat\n        mandatory\n            Connection\n                alternative\n                    "Peer 2 Peer"\n                    Server\n            Messages\n                or\n                    Text\n                    Video\n                    Audio\n        optional\n            "Data Storage"\n            "Media Player"\n\nconstraints\n    Server => "Data Storage"\n    Video | Audio => "Media Player"\n'
            )

    yield test_client

    with test_client.application.app_context():
        db.session.delete(dataset_test)
        db.session.delete(user_test)
        db.session.commit()
        shutil.rmtree(
            f"uploads/user_{user_test.id}/dataset_{dataset_test.id}", ignore_errors=True
        )


def create_user(email, password):
    user = User(email=email, password=password)
    db.session.add(user)
    db.session.commit()
    return user


def create_dataset(user_id):
    ds_meta_data = DSMetaData(
        title="Test Dataset",
        description="Test dataset description",
        publication_type=PublicationType.JOURNAL_ARTICLE,
    )
    db.session.add(ds_meta_data)
    db.session.commit()

    dataset = DataSet(user_id=user_id, ds_meta_data_id=ds_meta_data.id)
    db.session.add(dataset)
    db.session.commit()
    return dataset


def create_feature_model(dataset_id):
    feature_model = FeatureModel(data_set_id=dataset_id)
    db.session.add(feature_model)
    db.session.commit()
    return feature_model


def create_hubfile(name, feature_model_id, user_id, dataset_id):
    file_path = f"uploads/user_{user_id}/dataset_{dataset_id}/{name}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        f.write(
            "features\n"
            "    Chat\n"
            "        mandatory\n"
            "            Connection\n"
            "                alternative\n"
            '                    "Peer 2 Peer"\n'
            "                    Server\n"
            "            Messages\n"
            "                or\n"
            "                    Text\n"
            "                    Video\n"
            "                    Audio\n"
            "        optional\n"
            '            "Data Storage"\n'
            '            "Media Player"\n'
            "\n"
            "constraints\n"
            '    Server => "Data Storage"\n'
            '    Video | Audio => "Media Player"\n'
        )

    hubfile = Hubfile(
        name=name, checksum="123456", size=100, feature_model_id=feature_model_id
    )
    db.session.add(hubfile)
    db.session.commit()
    return hubfile


def delete_folder(user, dataset):
    if user.id != 2 or user.id != 1:
        shutil.rmtree(f"uploads/user_{user.id}", ignore_errors=True)
    else:
        shutil.rmtree(
            f"uploads/user_{user.id}/dataset_{dataset.id}", ignore_errors=True
        )


def test_download_all_datasets(test_client):
    user = create_user(email="test_user@example.com", password="password123")
    dataset = create_dataset(user_id=user.id)
    response = test_client.get("/dataset/download_all")

    assert (
        response.status_code == 200
    ), "La solicitud para descargar todos los datasets falló."
    assert (
        response.headers["Content-Type"] == "application/zip"
    ), "El tipo de contenido no es un archivo ZIP."
    assert (
        "all_datasets.zip" in response.headers["Content-Disposition"]
    ), "El archivo ZIP no tiene el nombre esperado."

    db.session.delete(dataset)
    db.session.delete(user)
    db.session.commit()
    delete_folder(user, dataset)


def test_to_glencoe(test_client):
    user = create_user(email="test_user_glencoe@example.com", password="password123")
    dataset = create_dataset(user_id=user.id)
    feature_model = create_feature_model(dataset_id=dataset.id)

    hubfile = create_hubfile(
        name="mock_dataset",
        feature_model_id=feature_model.id,
        user_id=user.id,
        dataset_id=dataset.id,
    )

    os.environ["WORKING_DIR"] = os.getcwd()

    temp_dir = "temp_glencoe"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Se actualiza el nombre del parámetro a glencoe_dir
        result = to_glencoe(file_id=hubfile.id, glencoe_dir=temp_dir)
        expected_path = os.path.join(temp_dir, f"{hubfile.name}_glencoe.txt")
        assert os.path.exists(
            result
        ), "El archivo transformado no se creó correctamente."
        assert (
            result == expected_path
        ), "La ruta del archivo transformado no es la esperada."
    finally:
        shutil.rmtree(temp_dir)

    db.session.delete(hubfile)
    db.session.delete(dataset)
    db.session.delete(user)
    db.session.commit()
    delete_folder(user, dataset)


def test_to_splot(test_client):
    user = create_user(email="test_user_splot@example.com", password="password123")
    dataset = create_dataset(user_id=user.id)

    feature_model = create_feature_model(dataset_id=dataset.id)

    hubfile = create_hubfile(
        name="mock_dataset",
        feature_model_id=feature_model.id,
        user_id=user.id,
        dataset_id=dataset.id,
    )

    os.environ["WORKING_DIR"] = os.getcwd()

    temp_dir = "temp_splot"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Se actualiza el nombre del parámetro a splot_dir
        result = to_splot(file_id=hubfile.id, splot_dir=temp_dir)
        expected_path = os.path.join(temp_dir, f"{hubfile.name}_splot.txt")
        assert os.path.exists(
            result
        ), "El archivo transformado no se creó correctamente."
        assert (
            result == expected_path
        ), "La ruta del archivo transformado no es la esperada."
    finally:
        shutil.rmtree(temp_dir)

    db.session.delete(hubfile)
    db.session.delete(dataset)
    db.session.delete(user)
    db.session.commit()
    delete_folder(user, dataset)


def test_to_cnf(test_client):
    user = create_user(email="test_user_cnf@example.com", password="password123")
    dataset = create_dataset(user_id=user.id)

    feature_model = create_feature_model(dataset_id=dataset.id)

    hubfile = create_hubfile(
        name="mock_dataset",
        feature_model_id=feature_model.id,
        user_id=user.id,
        dataset_id=dataset.id,
    )

    os.environ["WORKING_DIR"] = os.getcwd()

    temp_dir = "temp_cnf"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Se actualiza el nombre del parámetro a cnf_dir
        result = to_cnf(file_id=hubfile.id, cnf_dir=temp_dir)
        expected_path = os.path.join(temp_dir, f"{hubfile.name}_cnf.txt")
        assert os.path.exists(
            result
        ), "El archivo transformado no se creó correctamente."
        assert (
            result == expected_path
        ), "La ruta del archivo transformado no es la esperada."
    finally:
        shutil.rmtree(temp_dir)

    db.session.delete(hubfile)
    db.session.delete(feature_model)
    db.session.delete(dataset)
    db.session.delete(user)
    db.session.commit()
    delete_folder(user, dataset)
