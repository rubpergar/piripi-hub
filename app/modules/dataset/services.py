import logging
import os
import hashlib
import shutil
from typing import Optional
import uuid
import tempfile
from zipfile import ZipFile
from app.modules.hubfile.services import HubfileService
from flask import request
from flamapy.metamodels.fm_metamodel.transformations import UVLReader, GlencoeWriter, SPLOTWriter
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat, DimacsWriter
from app.modules.auth.services import AuthenticationService
from app.modules.dataset.models import DSViewRecord, DataSet, DSMetaData
from app.modules.dataset.repositories import (
    AuthorRepository,
    DOIMappingRepository,
    DSDownloadRecordRepository,
    DSMetaDataRepository,
    DSViewRecordRepository,
    DataSetRepository
)
from app.modules.featuremodel.repositories import FMMetaDataRepository, FeatureModelRepository
from app.modules.hubfile.repositories import (
    HubfileDownloadRecordRepository,
    HubfileRepository,
    HubfileViewRecordRepository
)
from core.services.BaseService import BaseService

logger = logging.getLogger(__name__)


def calculate_checksum_and_size(file_path):
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as file:
        content = file.read()
        hash_md5 = hashlib.md5(content).hexdigest()
        return hash_md5, file_size


class DataSetService(BaseService):
    def __init__(self):
        super().__init__(DataSetRepository())
        self.feature_model_repository = FeatureModelRepository()
        self.author_repository = AuthorRepository()
        self.dsmetadata_repository = DSMetaDataRepository()
        self.fmmetadata_repository = FMMetaDataRepository()
        self.dsdownloadrecord_repository = DSDownloadRecordRepository()
        self.hubfiledownloadrecord_repository = HubfileDownloadRecordRepository()
        self.hubfilerepository = HubfileRepository()
        self.dsviewrecord_repostory = DSViewRecordRepository()
        self.hubfileviewrecord_repository = HubfileViewRecordRepository()
        self.hubfile_service = HubfileService()

    def move_feature_models(self, dataset: DataSet):
        current_user = AuthenticationService().get_authenticated_user()
        source_dir = current_user.temp_folder()

        working_dir = os.getenv("WORKING_DIR", "")
        dest_dir = os.path.join(working_dir, "uploads", f"user_{current_user.id}", f"dataset_{dataset.id}")

        os.makedirs(dest_dir, exist_ok=True)

        for feature_model in dataset.feature_models:
            uvl_filename = feature_model.fm_meta_data.uvl_filename
            shutil.move(os.path.join(source_dir, uvl_filename), dest_dir)

    def is_synchronized(self, dataset_id: int) -> bool:
        return self.repository.is_synchronized(dataset_id)
    
    def get_synchronized(self, current_user_id: int) -> DataSet:
        return self.repository.get_synchronized(current_user_id)

    def get_unsynchronized(self, current_user_id: int) -> DataSet:
        return self.repository.get_unsynchronized(current_user_id)

    def get_unsynchronized_dataset(self, current_user_id: int, dataset_id: int) -> DataSet:
        return self.repository.get_unsynchronized_dataset(current_user_id, dataset_id)

    def latest_synchronized(self):
        return self.repository.latest_synchronized()

    def count_synchronized_datasets(self):
        return self.repository.count_synchronized_datasets()

    def count_feature_models(self):
        return self.feature_model_service.count_feature_models()

    def count_authors(self) -> int:
        return self.author_repository.count()

    def count_dsmetadata(self) -> int:
        return self.dsmetadata_repository.count()

    def total_dataset_downloads(self) -> int:
        return self.dsdownloadrecord_repository.total_dataset_downloads()

    def total_dataset_views(self) -> int:
        return self.dsviewrecord_repostory.total_dataset_views()

    def create_from_form(self, form, current_user) -> DataSet:
        main_author = {
            "name": f"{current_user.profile.surname}, {current_user.profile.name}",
            "affiliation": current_user.profile.affiliation,
            "orcid": current_user.profile.orcid,
        }
        try:
            logger.info(f"Creating dsmetadata...: {form.get_dsmetadata()}")
            dsmetadata = self.dsmetadata_repository.create(**form.get_dsmetadata())
            for author_data in [main_author] + form.get_authors():
                author = self.author_repository.create(commit=False, ds_meta_data_id=dsmetadata.id, **author_data)
                dsmetadata.authors.append(author)

            dataset = self.create(commit=False, user_id=current_user.id, ds_meta_data_id=dsmetadata.id)

            for feature_model in form.feature_models:
                uvl_filename = feature_model.uvl_filename.data
                fmmetadata = self.fmmetadata_repository.create(commit=False, **feature_model.get_fmmetadata())
                for author_data in feature_model.get_authors():
                    author = self.author_repository.create(commit=False, fm_meta_data_id=fmmetadata.id, **author_data)
                    fmmetadata.authors.append(author)

                fm = self.feature_model_repository.create(
                    commit=False, data_set_id=dataset.id, fm_meta_data_id=fmmetadata.id
                )

                # associated files in feature model
                file_path = os.path.join(current_user.temp_folder(), uvl_filename)
                checksum, size = calculate_checksum_and_size(file_path)

                file = self.hubfilerepository.create(
                    commit=False, name=uvl_filename, checksum=checksum, size=size, feature_model_id=fm.id
                )
                fm.files.append(file)
            self.repository.session.commit()
        except Exception as exc:
            logger.info(f"Exception creating dataset from form...: {exc}")
            self.repository.session.rollback()
            raise exc
        return dataset

    def update_dsmetadata(self, id, **kwargs):
        return self.dsmetadata_repository.update(id, **kwargs)

    def get_uvlhub_doi(self, dataset: DataSet) -> str:
        domain = os.getenv('DOMAIN', 'localhost')
        return f'http://{domain}/doi/{dataset.ds_meta_data.dataset_doi}'
    
    def zip_all_datasets(self) -> str:
        temp_dir = tempfile.mkdtemp() 
        zip_path = os.path.join(temp_dir, "all_datasets.zip") 

        with ZipFile(zip_path, "w") as zipf: 
            for zz in os.listdir("uploads"): 
                user_path = os.path.join("uploads", zz)

                if os.path.isdir(user_path) and zz.startswith("user_"):  
                    for dataset_dir in os.listdir(user_path): 
                        dataset_path = os.path.join(user_path, dataset_dir)

                        if os.path.isdir(dataset_path) and dataset_dir.startswith("dataset_"): 
                            dataset_id = int(dataset_dir.split("_")[1])

                            if self.is_synchronized(dataset_id): 
                                print(f"Adding dataset: {dataset_dir}") 

                                for subdir, dirs, files in os.walk(dataset_path):
                                    for file in files:
                                        full_path = os.path.join(subdir, file)
                                        relative_path = os.path.relpath(full_path, dataset_path)


                                        if file.endswith('.uvl'):

                                            dataset_name = os.path.basename(dataset_dir)
                                            print(f"Dataset name: {dataset_name}")
                                            zipf.write(full_path, arcname=os.path.join(dataset_name, relative_path))

                                            self.convert_and_add_to_zip(zipf, dataset_id, file, dataset_name)
        return zip_path


    def get_hubfile_by_uvl_filename(self, dataset_id, uvl_filename):
        dataset = self.repository.get(dataset_id)  

        if not dataset:
            raise FileNotFoundError(f"Dataset with ID {dataset_id} not found")

        for feature_model in dataset.feature_models:
            for file in feature_model.files: 
                if file.name == uvl_filename:
                    return file 

        raise FileNotFoundError(f"UVL file {uvl_filename} not found in dataset {dataset_id}")
    
    def convert_and_add_to_zip(self, zipf, dataset_id, uvl_filename, dataset_dir):
        formats = ['glencoe', 'splot', 'cnf']
        for conversion_type in formats:
            self.add_converted_file_to_zip(zipf, dataset_id, uvl_filename, conversion_type, dataset_dir)

    def add_converted_file_to_zip(self, zipf, dataset_id, uvl_filename, conversion_type, dataset_dir):
        temp_file = tempfile.NamedTemporaryFile(suffix=f'.{conversion_type}', delete=False)
        try:
            if conversion_type == "glencoe":
                self.convert_to_glencoe(dataset_id, uvl_filename, temp_file.name)
            elif conversion_type == "splot":
                self.convert_to_splot(dataset_id, uvl_filename, temp_file.name)
            elif conversion_type == "cnf":
                self.convert_to_cnf(dataset_id, uvl_filename, temp_file.name)

            zipf.write(temp_file.name, arcname=os.path.join(dataset_dir, f"{os.path.splitext(uvl_filename)[0]}_{conversion_type}.txt"))
        finally:
            os.remove(temp_file.name)

    def convert_uvl_to_format(self, dataset_id, uvl_filename, conversion_type, temp_filename):
        """Método que enruta la conversión del archivo UVL al formato adecuado."""
        if conversion_type == "glencoe":
            self.convert_to_glencoe(dataset_id, uvl_filename, temp_filename)
        elif conversion_type == "splot":
            self.convert_to_splot(dataset_id, uvl_filename, temp_filename)
        elif conversion_type == "cnf":
            self.convert_to_cnf(dataset_id, uvl_filename, temp_filename)
        else:
            raise ValueError(f"Unsupported conversion type: {conversion_type}")
        
    def convert_to_glencoe(self, dataset_id, uvl_filename, temp_filename):
        hubfile = self.get_hubfile_by_uvl_filename(dataset_id, uvl_filename)
        fm = UVLReader(hubfile.get_path()).transform()
        GlencoeWriter(temp_filename, fm).transform()

    def convert_to_splot(self, dataset_id, uvl_filename, temp_filename):
        hubfile = self.get_hubfile_by_uvl_filename(dataset_id, uvl_filename)
        fm = UVLReader(hubfile.get_path()).transform()
        SPLOTWriter(temp_filename, fm).transform()

    def convert_to_cnf(self, dataset_id, uvl_filename, temp_filename):
        hubfile = self.get_hubfile_by_uvl_filename(dataset_id, uvl_filename)
        fm = UVLReader(hubfile.get_path()).transform()
        sat = FmToPysat(fm).transform()
        DimacsWriter(temp_filename, sat).transform()

    

class AuthorService(BaseService):
    def __init__(self):
        super().__init__(AuthorRepository())


class DSDownloadRecordService(BaseService):
    def __init__(self):
        super().__init__(DSDownloadRecordRepository())


class DSMetaDataService(BaseService):
    def __init__(self):
        super().__init__(DSMetaDataRepository())

    def update(self, id, **kwargs):
        return self.repository.update(id, **kwargs)

    def filter_by_doi(self, doi: str) -> Optional[DSMetaData]:
        return self.repository.filter_by_doi(doi)


class DSViewRecordService(BaseService):
    def __init__(self):
        super().__init__(DSViewRecordRepository())

    def the_record_exists(self, dataset: DataSet, user_cookie: str):
        return self.repository.the_record_exists(dataset, user_cookie)

    def create_new_record(self, dataset: DataSet,  user_cookie: str) -> DSViewRecord:
        return self.repository.create_new_record(dataset, user_cookie)

    def create_cookie(self, dataset: DataSet) -> str:

        user_cookie = request.cookies.get("view_cookie")
        if not user_cookie:
            user_cookie = str(uuid.uuid4())

        existing_record = self.the_record_exists(dataset=dataset, user_cookie=user_cookie)

        if not existing_record:
            self.create_new_record(dataset=dataset, user_cookie=user_cookie)

        return user_cookie


class DOIMappingService(BaseService):
    def __init__(self):
        super().__init__(DOIMappingRepository())

    def get_new_doi(self, old_doi: str) -> str:
        doi_mapping = self.repository.get_new_doi(old_doi)
        if doi_mapping:
            return doi_mapping.dataset_doi_new
        else:
            return None


class SizeService():

    def __init__(self):
        pass

    def get_human_readable_size(self, size: int) -> str:
        if size < 1024:
            return f'{size} bytes'
        elif size < 1024 ** 2:
            return f'{round(size / 1024, 2)} KB'
        elif size < 1024 ** 3:
            return f'{round(size / (1024 ** 2), 2)} MB'
        else:
            return f'{round(size / (1024 ** 3), 2)} GB'
