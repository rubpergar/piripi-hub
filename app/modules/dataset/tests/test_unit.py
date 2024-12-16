import io
import shutil
from zipfile import ZipFile
import pytest
import os
import json
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

"""
-------------------------
HELPERS
-------------------------

"""


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
                'features\n    Chat\n        mandatory\n            Connection\n                alternative\n                    "Peer 2 Peer"\n                    Server\n            Messages\n                or\n                    Text\n                    Video\n                    Audio\n        optional\n            "Data Storage"\n            "Media Player"\n\nconstraints\n    Server => "Data Storage"\n    Video | Audio => "Media Player"\n'  # noqa
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


"""
-------------------------
FEATURE
-------------------------

"""


def test_download_all_datasets(test_client):
    user = create_user(email="test_user@example.com", password="password123")
    dataset = create_dataset(user_id=user.id)
    response = test_client.get("/dataset/download/all")

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


"""
-------------------------
PARSING
-------------------------

"""


@pytest.mark.parametrize(
    "file_type, expected_extension",
    [("uvl", "_glencoe.txt"), ("txt", "_splot.txt"), ("xml", "_cnf.txt")],
)
def test_file_conversion(test_client, file_type, expected_extension):
    user = create_user(
        email=f"test_user_{file_type}_parsing@example.com", password="password123"
    )
    dataset = create_dataset(user_id=user.id)
    feature_model = create_feature_model(dataset.id)

    hubfile = create_hubfile(
        f"file100.{file_type}", feature_model.id, user.id, dataset.id
    )

    os.environ["WORKING_DIR"] = os.getcwd()
    temp_dir = "temp_files"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        if file_type == "uvl":
            result = to_glencoe(file_id=hubfile.id, glencoe_dir=temp_dir)
        elif file_type == "txt":
            result = to_splot(file_id=hubfile.id, splot_dir=temp_dir)
        elif file_type == "xml":
            result = to_cnf(file_id=hubfile.id, cnf_dir=temp_dir)

        expected_path = os.path.join(temp_dir, f"{hubfile.name}{expected_extension}")

        assert os.path.exists(result), "El archivo no fue creado correctamente."
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


def test_other_file_extension(test_client):
    user = create_user(email="test_user_others@example.com", password="password123")
    dataset = create_dataset(user_id=user.id)

    os.makedirs(f"uploads/user_{user.id}/dataset_{dataset.id}", exist_ok=True)
    with open(f"uploads/user_{user.id}/dataset_{dataset.id}/file100.txt", "w") as f:
        f.write("Este es un archivo con una extensión diferente para prueba.")

    response = test_client.get("/dataset/download/all")

    assert (
        response.status_code == 200
    ), "La solicitud para descargar todos los datasets falló."

    # Usar BytesIO para tratar la respuesta como un archivo
    zip_data = io.BytesIO(response.data)

    with ZipFile(zip_data) as zipf:
        file_list = zipf.namelist()
        assert any(
            "otros/file100.txt" in file for file in file_list
        ), "El archivo con extensión .txt no se encontró en la carpeta 'otros'."

    db.session.delete(dataset)
    db.session.delete(user)
    db.session.commit()
    delete_folder(user, dataset)


def test_to_glencoe_parsing(test_client):
    user = create_user(
        email="test_user_glencoe_parsing@example.com", password="password123"
    )
    dataset = create_dataset(user_id=user.id)
    feature_model = create_feature_model(dataset_id=dataset.id)

    uvl_file_path = f"uploads/user_{user.id}/dataset_{dataset.id}/file100.uvl"
    os.makedirs(os.path.dirname(uvl_file_path), exist_ok=True)
    with open(uvl_file_path, "w") as f:
        f.write(
            'features\n    Chat\n        mandatory\n            Connection\n                alternative\n                    "Peer 2 Peer"\n                    Server\n            Messages\n                or\n                    Text\n                    Video\n                    Audio\n        optional\n            "Data Storage"\n            "Media Player"\n\nconstraints\n    Server => "Data Storage"\n    Video | Audio => "Media Player"\n'
        )

    hubfile = create_hubfile(
        name="file100.uvl",
        feature_model_id=feature_model.id,
        user_id=user.id,
        dataset_id=dataset.id,
    )

    os.environ["WORKING_DIR"] = os.getcwd()
    temp_dir = "temp_glencoe"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        result = to_glencoe(file_id=hubfile.id, glencoe_dir=temp_dir)

        glencoe_file_path = os.path.join(temp_dir, f"{hubfile.name}_glencoe.txt")

        with open(glencoe_file_path, "r") as f:
            glencoe_content = f.read()

        try:
            glencoe_data = json.loads(glencoe_content)
        except json.JSONDecodeError:
            assert False, "El contenido del archivo .glencoe no es un JSON válido."

    finally:
        shutil.rmtree(temp_dir)

    db.session.delete(hubfile)
    db.session.delete(dataset)
    db.session.delete(user)
    db.session.commit()
    delete_folder(user, dataset)


def test_to_splot_parsing(test_client):
    user = create_user(
        email="test_user_splot_parsing@example.com", password="password123"
    )
    dataset = create_dataset(user_id=user.id)
    feature_model = create_feature_model(dataset_id=dataset.id)

    uvl_file_path = f"uploads/user_{user.id}/dataset_{dataset.id}/file100.uvl"
    os.makedirs(os.path.dirname(uvl_file_path), exist_ok=True)
    with open(uvl_file_path, "w") as f:
        f.write(
            'features\n    Chat\n        mandatory\n            Connection\n                alternative\n                    "Peer 2 Peer"\n                    Server\n            Messages\n                or\n                    Text\n                    Video\n                    Audio\n        optional\n            "Data Storage"\n            "Media Player"\n\nconstraints\n    Server => "Data Storage"\n    Video | Audio => "Media Player"\n'
        )

    hubfile = create_hubfile(
        name="file100.uvl",
        feature_model_id=feature_model.id,
        user_id=user.id,
        dataset_id=dataset.id,
    )

    os.environ["WORKING_DIR"] = os.getcwd()
    temp_dir = "temp_splot"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        result = to_splot(file_id=hubfile.id, splot_dir=temp_dir)

        splot_file_path = os.path.join(temp_dir, f"{hubfile.name}_splot.txt")
        assert os.path.exists(splot_file_path), "El archivo .splot.txt no fue creado."

        with open(splot_file_path, "r") as f:
            splot_content = f.read()

        expected_splot_content = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<feature_model name="Chat">
<feature_tree>
:r Chat (Chat)
	:m Connection (Connection)
		:g [1,1]
			: "Peer 2 Peer" ("Peer 2 Peer")
			: Server (Server)
	:m Messages (Messages)
		:g [1,3]
			: Text (Text)
			: Video (Video)
			: Audio (Audio)
	:o "Data Storage" ("Data Storage")
	:o "Media Player" ("Media Player")
</feature_tree>
<constraints>
	C1: ~Server or "Data Storage"
	C2: ~Video or "Media Player"
	C3: ~Audio or "Media Player"
</constraints>
</feature_model>"""

        assert (
            expected_splot_content.strip() == splot_content.strip()
        ), "El contenido del archivo .splot.txt no es el esperado."

    finally:
        shutil.rmtree(temp_dir)

    db.session.delete(hubfile)
    db.session.delete(dataset)
    db.session.delete(user)
    db.session.commit()
    delete_folder(user, dataset)


def test_to_cnf_parsing(test_client):
    user = create_user(
        email="test_user_cnf_parsing@example.com", password="password123"
    )
    dataset = create_dataset(user_id=user.id)
    feature_model = create_feature_model(dataset_id=dataset.id)

    uvl_file_path = f"uploads/user_{user.id}/dataset_{dataset.id}/file100.uvl"
    os.makedirs(os.path.dirname(uvl_file_path), exist_ok=True)
    with open(uvl_file_path, "w") as f:
        f.write(
            'features\n    Chat\n        mandatory\n            Connection\n                alternative\n                    "Peer 2 Peer"\n                    Server\n            Messages\n                or\n                    Text\n                    Video\n                    Audio\n        optional\n            "Data Storage"\n            "Media Player"\n\nconstraints\n    Server => "Data Storage"\n    Video | Audio => "Media Player"\n'
        )

    hubfile = create_hubfile(
        name="file100.uvl",
        feature_model_id=feature_model.id,
        user_id=user.id,
        dataset_id=dataset.id,
    )

    os.environ["WORKING_DIR"] = os.getcwd()
    temp_dir = "temp_cnf"
    os.makedirs(temp_dir, exist_ok=True)

    try:
        result = to_cnf(file_id=hubfile.id, cnf_dir=temp_dir)

        cnf_file_path = os.path.join(temp_dir, f"{hubfile.name}_cnf.txt")
        assert os.path.exists(cnf_file_path), "El archivo .cnf no fue creado."

        with open(cnf_file_path, "r") as f:
            cnf_content = f.read()

        expected_cnf_content = """p cnf 10 18
c 1 Chat
c 2 Connection
c 3 "Peer 2 Peer"
c 4 Server
c 5 Messages
c 6 Text
c 7 Video
c 8 Audio
c 9 "Data Storage"
c 10 "Media Player"
1 0
-1 2 0
-2 1 0
-2 3 4 0
-3 -4 0
-3 2 0
-4 2 0
-1 5 0
-5 1 0
-5 6 7 8 0
-6 5 0
-7 5 0
-8 5 0
-9 1 0
-10 1 0
-4 9 0
-7 10 0
-8 10 0"""

        assert (
            expected_cnf_content.strip() == cnf_content.strip()
        ), "El contenido del archivo .cnf no es el esperado."

    finally:
        shutil.rmtree(temp_dir)

    db.session.delete(hubfile)
    db.session.delete(dataset)
    db.session.delete(user)
    db.session.commit()
    delete_folder(user, dataset)
