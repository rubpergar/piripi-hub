import pytest
from unittest import mock
from app.modules.dataset.services import DataSetService
from app.modules.dataset.models import DataSet
from app.modules.featuremodel.models import FeatureModel
from app.modules.hubfile.models import Hubfile
import tempfile
import os
from zipfile import ZipFile


@pytest.fixture
def mock_dataset_service():
    """Fixture para crear una instancia de DataSetService con mocks"""
    service = DataSetService()

    service.repository = mock.Mock()
    service.is_synchronized = mock.Mock()
    return service


@pytest.fixture
def mock_dataset_with_files():
    """Fixture para crear un dataset con files y feature models"""
    dataset = DataSet(id=1, user_id=1)
    feature_model = FeatureModel(id=1, data_set_id=1)
    file1 = Hubfile(id=1, name="file1.uvl")
    file2 = Hubfile(id=2, name="file2.uvl")
    feature_model.files = [file1, file2]
    dataset.feature_models = [feature_model]
    return dataset


def test_zip_all_datasets():
    obj = DataSetService()

    with mock.patch.object(obj, 'is_synchronized', return_value=True), \
         mock.patch.object(obj, 'convert_and_add_to_zip') as mock_convert_and_add:

        with tempfile.TemporaryDirectory() as temp_dir:
            uploads_dir = os.path.join(temp_dir, 'uploads')
            os.makedirs(uploads_dir)

            user_dir = os.path.join(uploads_dir, 'user_123')
            os.makedirs(user_dir)

            dataset_dir = os.path.join(user_dir, 'dataset_1')
            os.makedirs(dataset_dir)

            uvl_files = ['file1.uvl', 'file2.uvl', 'file3.uvl']
            for file_name in uvl_files:
                uvl_file = os.path.join(dataset_dir, file_name)
                with open(uvl_file, 'w') as f:
                    f.write("dummy data")

            zip_path = obj.zip_all_datasets()

            assert os.path.exists(zip_path)
            with ZipFile(zip_path, 'r') as zipf:
                for file_name in uvl_files:
                    expected_path = f'dataset_1/{file_name}'
                    zip_files = zipf.namelist()
                    print(zip_files)
                    assert expected_path in zip_files, f"Expected file path {expected_path} not found in {zip_files}"

            assert mock_convert_and_add.call_count == len(uvl_files) * 4

            for file_name in uvl_files:
                for conversion_type in ['uvl', 'glencoe', 'splot', 'cnf']:
                    mock_convert_and_add.assert_any_call(mock.ANY, 1, file_name, 'dataset_1')


def test_get_hubfile_by_uvl_filename(mock_dataset_service, mock_dataset_with_files):
    """Prueba para get_hubfile_by_uvl_filename"""
    mock_dataset_service.repository.get.return_value = mock_dataset_with_files

    file = mock_dataset_service.get_hubfile_by_uvl_filename(1, "file1.uvl")
    assert file.name == "file1.uvl"

    with pytest.raises(FileNotFoundError):
        mock_dataset_service.get_hubfile_by_uvl_filename(1, "non_existent_file.uvl")


@mock.patch('app.modules.dataset.services.DataSetService.convert_to_glencoe')
@mock.patch('app.modules.dataset.services.DataSetService.convert_to_splot')
@mock.patch('app.modules.dataset.services.DataSetService.convert_to_cnf')
def test_convert_and_add_to_zip(
    mock_convert_cnf, mock_convert_splot, mock_convert_glencoe,
    mock_dataset_service, mock_dataset_with_files
):
    """Prueba para convert_and_add_to_zip"""

    mock_dataset_service.is_synchronized.return_value = True
    mock_dataset_service.repository.get.return_value = mock_dataset_with_files

    with mock.patch("zipfile.ZipFile") as mock_zip:
        mock_zip.return_value.__enter__.return_value = mock.MagicMock()
        mock_dataset_service.convert_and_add_to_zip(
            mock_zip.return_value.__enter__.return_value, 1, "file1.uvl", "dataset_1")

        mock_convert_glencoe.assert_called_once()
        mock_convert_splot.assert_called_once()
        mock_convert_cnf.assert_called_once()


@pytest.mark.parametrize("conversion_type, method", [
    ("glencoe", "convert_to_glencoe"),
    ("splot", "convert_to_splot"),
    ("cnf", "convert_to_cnf")
])
def test_convert_uvl_to_format(mock_dataset_service, conversion_type, method):
    """Prueba para convertir el archivo UVL a diferentes formatos"""

    mock_dataset_service.get_hubfile_by_uvl_filename = mock.Mock()
    mock_dataset_service.get_hubfile_by_uvl_filename.return_value.get_path.return_value = "/mock/path/to/uvl"

    with mock.patch.object(mock_dataset_service, method) as mock_conversion:
        mock_dataset_service.convert_uvl_to_format(1, "file1.uvl", conversion_type, "/mock/temp/file")

        mock_conversion.assert_called_once_with(1, "file1.uvl", "/mock/temp/file")
