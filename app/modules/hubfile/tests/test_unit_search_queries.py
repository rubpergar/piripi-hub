import pytest
from unittest import mock
from app.modules.hubfile.models import Hubfile
import io
import zipfile


# ===== Fixtures =====
@pytest.fixture
def mock_hubfile_service():
    """Crea una instancia de HubfileService con métodos simulados"""
    service = mock.Mock()
    return service


@pytest.fixture
def mock_files():
    """Crea un conjunto de archivos Hubfile simulados"""
    file1 = Hubfile(id=1, name="file1.uvl")
    file2 = Hubfile(id=2, name="file2.uvl")
    file3 = Hubfile(id=3, name="file3.uvl")
    return [file1, file2, file3]


# ===== Tests =====
def test_zip_with_valid_models_ids(mock_hubfile_service, mock_files):
    """Prueba para generar un ZIP con IDs válidos"""

    mock_hubfile_service.get_or_404.side_effect = lambda file_id: next(f for f in mock_files if f.id == file_id)

    file_ids = [1, 2]
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file_id in file_ids:
            file = mock_hubfile_service.get_or_404(file_id)
            filename = file.name
            file_content = f"Dummy content for {filename}".encode()
            zip_file.writestr(filename, file_content)

    # Validación del ZIP
    zip_buffer.seek(0)
    with zipfile.ZipFile(zip_buffer, "r") as zip_file:
        zip_files = zip_file.namelist()
        assert len(zip_files) == len(file_ids), f"Esperado {len(file_ids)} archivos en el ZIP, encontrado {len(zip_files)}"
        for file_id in file_ids:
            expected_filename = f"file{file_id}.uvl"
            assert expected_filename in zip_files, f"{expected_filename} no se encontró en el ZIP"


def test_generate_zip_filename():
    """Prueba para generar el nombre del archivo ZIP"""

    file_ids = [1, 2, 3]
    expected_filename = "models_1_2_3.zip"
    generated_filename = f"models_{'_'.join(str(file_id) for file_id in file_ids)}.zip"
    assert generated_filename == expected_filename, f"Nombre esperado: {expected_filename}, obtenido: {generated_filename}"


def test_invalid_file_ids():
    """Prueba para manejar IDs de con formato inválido"""

    invalid_ids = ["abc", "123xyz"]
    with pytest.raises(ValueError):
        [int(file_id.strip()) for file_id in invalid_ids]


def test_generate_zip_with_empty_file_ids(mock_hubfile_service):
    """Prueba para manejar el caso de IDs vacíos"""

    file_ids = []
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file_id in file_ids:
            pass  # No se agregarán archivos

    zip_buffer.seek(0)
    with zipfile.ZipFile(zip_buffer, "r") as zip_file:
        zip_files = zip_file.namelist()
        assert len(zip_files) == 0, f"Esperado 0 archivos en el ZIP, encontrado {len(zip_files)}"


def test_generate_zip_with_unexisting_file_ids(mock_hubfile_service, mock_files):
    """Prueba para manejar IDs inexistentes"""

    mock_hubfile_service.get_or_404.side_effect = lambda file_id: next(f for f in mock_files if f.id == file_id)

    file_ids = [99999, 100000]
    zip_buffer = io.BytesIO()

    with pytest.raises(StopIteration):
        with zipfile.ZipFile(zip_buffer, "w") as zip_file:
            for file_id in file_ids:
                file = mock_hubfile_service.get_or_404(file_id)
                filename = file.name
                file_content = f"Dummy content for {filename}".encode()
                zip_file.writestr(filename, file_content)


def test_generate_zip_with_mixed_valid_and_invalid_file_ids(mock_hubfile_service, mock_files):
    """Prueba para manejar una mezcla de IDs válidos e inválidos"""

    mock_hubfile_service.get_or_404.side_effect = lambda file_id: next(f for f in mock_files if f.id == file_id)

    file_ids = [1, 99999]
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file_id in file_ids:
            try:
                file = mock_hubfile_service.get_or_404(file_id)
                filename = file.name
                file_content = f"Dummy content for {filename}".encode()
                zip_file.writestr(filename, file_content)
            except StopIteration:
                pass  # Ignorar IDs no válidos

    zip_buffer.seek(0)
    with zipfile.ZipFile(zip_buffer, "r") as zip_file:
        zip_files = zip_file.namelist()
        assert len(zip_files) == 1, f"Esperado 1 archivo válido en el ZIP, encontrado {len(zip_files)}"
        assert "file1.uvl" in zip_files, "file1.uvl no se encontró en el ZIP"
