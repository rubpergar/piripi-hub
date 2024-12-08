import logging
import os
import json
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from zipfile import ZipFile
from flask import send_file
from flask_login import login_required, current_user
from app import db
from flamapy.metamodels.fm_metamodel.transformations import UVLReader, GlencoeWriter, SPLOTWriter
from flamapy.metamodels.pysat_metamodel.transformations import FmToPysat, DimacsWriter

from flask import (
    redirect,
    render_template,
    request,
    jsonify,
    send_from_directory,
    make_response,
    abort,
    url_for,
    flash
)

from app.modules.dataset.forms import DataSetForm
from app.modules.dataset.forms import DataSetForm
from app.modules.dataset.forms import RateForm
from app.modules.dataset.models import (
    DSDownloadRecord
)
from app.modules.dataset import dataset_bp
from app.modules.dataset.services import (
    AuthorService,
    DSDownloadRecordService,
    DSMetaDataService,
    DSViewRecordService,
    DataSetService,
    DOIMappingService,
    RateDataSetService
)
from app.modules.hubfile.services import HubfileService
from app.modules.zenodo.services import ZenodoService

logger = logging.getLogger(__name__)


dataset_service = DataSetService()
author_service = AuthorService()
dsmetadata_service = DSMetaDataService()
zenodo_service = ZenodoService()
doi_mapping_service = DOIMappingService()
ds_view_record_service = DSViewRecordService()
rateDataset_service = RateDataSetService()


@dataset_bp.route("/dataset/upload", methods=["GET", "POST"])
@login_required
def create_dataset():
    form = DataSetForm()
    if request.method == "POST":

        dataset = None

        if not form.validate_on_submit():
            return jsonify({"message": form.errors}), 400

        try:
            logger.info("Creating dataset...")
            dataset = dataset_service.create_from_form(form=form, current_user=current_user)
            logger.info(f"Created dataset: {dataset}")
            dataset_service.move_feature_models(dataset)
        except Exception as exc:
            logger.exception(f"Exception while create dataset data in local {exc}")
            return jsonify({"Exception while create dataset data in local: ": str(exc)}), 400

        # send dataset as deposition to Zenodo
        data = {}
        try:
            zenodo_response_json = zenodo_service.create_new_deposition(dataset)
            response_data = json.dumps(zenodo_response_json)
            data = json.loads(response_data)
        except Exception as exc:
            data = {}
            zenodo_response_json = {}
            logger.exception(f"Exception while create dataset data in Zenodo {exc}")

        if data.get("conceptrecid"):
            deposition_id = data.get("id")

            # update dataset with deposition id in Zenodo
            dataset_service.update_dsmetadata(dataset.ds_meta_data_id, deposition_id=deposition_id)

            try:
                # iterate for each feature model (one feature model = one request to Zenodo)
                for feature_model in dataset.feature_models:
                    zenodo_service.upload_file(dataset, deposition_id, feature_model)

                # publish deposition
                zenodo_service.publish_deposition(deposition_id)

                # update DOI
                deposition_doi = zenodo_service.get_doi(deposition_id)
                dataset_service.update_dsmetadata(dataset.ds_meta_data_id, dataset_doi=deposition_doi)
            except Exception as e:
                msg = f"it has not been possible upload feature models in Zenodo and update the DOI: {e}"
                return jsonify({"message": msg}), 200

        # Delete temp folder
        file_path = current_user.temp_folder()
        if os.path.exists(file_path) and os.path.isdir(file_path):
            shutil.rmtree(file_path)

        msg = "Everything works!"
        return jsonify({"message": msg}), 200

    return render_template("dataset/upload_dataset.html", form=form)


@dataset_bp.route("/dataset/list", methods=["GET", "POST"])
@login_required
def list_dataset():
    return render_template(
        "dataset/list_datasets.html",
        datasets=dataset_service.get_synchronized(current_user.id),
        local_datasets=dataset_service.get_unsynchronized(current_user.id),
    )


@dataset_bp.route("/dataset/file/upload", methods=["POST"])
@login_required
def upload():
    file = request.files["file"]
    temp_folder = current_user.temp_folder()

    if not file or not file.filename.endswith(".uvl"):
        return jsonify({"message": "No valid file"}), 400

    # create temp folder
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    file_path = os.path.join(temp_folder, file.filename)

    if os.path.exists(file_path):
        # Generate unique filename (by recursion)
        base_name, extension = os.path.splitext(file.filename)
        i = 1
        while os.path.exists(
            os.path.join(temp_folder, f"{base_name} ({i}){extension}")
        ):
            i += 1
        new_filename = f"{base_name} ({i}){extension}"
        file_path = os.path.join(temp_folder, new_filename)
    else:
        new_filename = file.filename

    try:
        file.save(file_path)
    except Exception as e:
        return jsonify({"message": str(e)}), 500

    return (
        jsonify(
            {
                "message": "UVL uploaded and validated successfully",
                "filename": new_filename,
            }
        ),
        200,
    )


@dataset_bp.route("/dataset/file/delete", methods=["POST"])
def delete():
    data = request.get_json()
    filename = data.get("file")
    temp_folder = current_user.temp_folder()
    filepath = os.path.join(temp_folder, filename)

    if os.path.exists(filepath):
        os.remove(filepath)
        return jsonify({"message": "File deleted successfully"})

    return jsonify({"error": "Error: File not found"})


@dataset_bp.route("/dataset/download_all", methods=["GET"])
def download_all_datasets():
    datasets = dataset_service.get_all_datasets()
    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, "all_datasets.zip")

    # Creamos los directorios para cada tipo de archivo
    uvl_dir = os.path.join(temp_dir, "uvl")
    cnf_dir = os.path.join(temp_dir, "cnf")
    splot_dir = os.path.join(temp_dir, "splot")
    glencoe_dir = os.path.join(temp_dir, "glencoe")

    os.makedirs(uvl_dir, exist_ok=True)
    os.makedirs(cnf_dir, exist_ok=True)
    os.makedirs(splot_dir, exist_ok=True)
    os.makedirs(glencoe_dir, exist_ok=True)

    try:
        with ZipFile(zip_path, "w") as zipf:
            for dataset in datasets:
                file_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"
                for subdir, dirs, files in os.walk(file_path):
                    for file in files:
                        full_path = os.path.join(subdir, file)
                        relative_path = os.path.relpath(full_path, file_path)

                        # Identificamos la extensión del archivo
                        _, ext = os.path.splitext(file)
                        ext = ext.lower()

                        if ext == ".uvl":
                            # Copiamos el archivo uvl a la carpeta uvl
                            uvl_file_path = os.path.join(uvl_dir, relative_path)
                            os.makedirs(os.path.dirname(uvl_file_path), exist_ok=True)
                            shutil.copy(full_path, uvl_file_path)
                            zipf.write(
                                uvl_file_path,
                                arcname=os.path.relpath(uvl_file_path, temp_dir),
                            )
                            logging.debug(f"Archivo UVL agregado al zip: {relative_path}")

                            # Obtenemos el ID del archivo UVL para las transformaciones
                            try:
                                file_id = int(file.split(".")[0][4:])
                            except ValueError:
                                logging.error(f"No se puede extraer el ID del archivo: {file}")
                                continue

                            # Transformaciones del archivo UVL
                            try:
                                cnf_dataset = to_cnf(file_id, cnf_dir)
                                splot_dataset = to_splot(file_id, splot_dir)
                                glencoe_dataset = to_glencoe(file_id, glencoe_dir)

                                # Agregamos los archivos transformados si existen
                                for transformed_file in [cnf_dataset, splot_dataset, glencoe_dataset]:
                                    if os.path.exists(transformed_file):
                                        zipf.write(
                                            transformed_file,
                                            arcname=os.path.relpath(transformed_file, temp_dir),
                                        )
                            except Exception as e:
                                logging.error(f"No se ha podido transformar el archivo {file}: {e}")
                                continue
                        else:
                            # Si no es UVL (por si existen otros archivos), los podemos ignorar
                            # o guardarlos en otra carpeta según se requiera.
                            # Aquí simplemente los copiamos a la carpeta correspondiente a su extensión
                            # si se desea. Ejemplo:
                            target_dir = None
                            if ext == ".cnf":
                                target_dir = cnf_dir
                            elif ext == ".splot":
                                target_dir = splot_dir
                            elif ext == ".glencoe":
                                target_dir = glencoe_dir
                            else:
                                # Si es otro tipo de archivo, podríamos crear una carpeta "otros"
                                # o simplemente ignorar.
                                continue

                            target_file_path = os.path.join(target_dir, relative_path)
                            os.makedirs(os.path.dirname(target_file_path), exist_ok=True)
                            shutil.copy(full_path, target_file_path)
                            zipf.write(
                                target_file_path,
                                arcname=os.path.relpath(target_file_path, temp_dir),
                            )
                            logging.debug(f"Archivo {ext} agregado al zip: {relative_path}")


        return send_file(
            zip_path,
            as_attachment=True,
            mimetype="application/zip",
            download_name="all_datasets.zip",
        )
    finally:
        shutil.rmtree(temp_dir)


def to_glencoe(file_id, glencoe_dir):
    hubfile = HubfileService().get_by_id(file_id)
    model = UVLReader(hubfile.get_path()).transform()
    glencoe_file_name = f"{hubfile.name}_glencoe.txt"
    glencoe_full_path = os.path.join(glencoe_dir, glencoe_file_name)
    GlencoeWriter(glencoe_full_path, model).transform()
    return glencoe_full_path


def to_splot(file_id, splot_dir):
    hubfile = HubfileService().get_by_id(file_id)
    model = UVLReader(hubfile.get_path()).transform()
    splot_file_name = f"{hubfile.name}_splot.txt"
    splot_full_path = os.path.join(splot_dir, splot_file_name)
    SPLOTWriter(splot_full_path, model).transform()
    return splot_full_path


def to_cnf(file_id, cnf_dir):
    hubfile = HubfileService().get_by_id(file_id)
    model = UVLReader(hubfile.get_path()).transform()
    sat = FmToPysat(model).transform()
    cnf_file_name = f"{hubfile.name}_cnf.txt"
    cnf_full_path = os.path.join(cnf_dir, cnf_file_name)
    DimacsWriter(cnf_full_path, sat).transform()
    return cnf_full_path

@dataset_bp.route("/rate/<int:dataset_id>", methods=["GET"], endpoint="rate")
# @login_required
def viewRates(dataset_id):
    form = RateForm()
    ratedata = rateDataset_service.get_all_comments(dataset_id)
    return render_template('rate/index.html', rate_data_sets=ratedata, form=form, dataset=dataset_id)
'''
CREATE
'''
@dataset_bp.route('/ratedataset/create/<int:dataset_id>', methods=['GET', 'POST'], endpoint="create_ratedataset")
@login_required
def create_rate(dataset_id):
    form = RateForm()
    if form.validate_on_submit():
        result = rateDataset_service.create(
            rate=form.rate.data,
            comment=form.comment.data,
            user_id=current_user.id,
            dataset_id=dataset_id
        )
        return rateDataset_service.handle_service_response2(
            result=result,
            errors=form.errors,
            success_url_redirect='dataset.rate',
            success_msg='Rate successfully published!',
            error_template='rate/create.html',
            form=form,
            id=dataset_id
        )
    return render_template('rate/create.html', form=form, dataset=dataset_id)


@dataset_bp.route('/ratedataset/edit/<int:dataset_id>/<int:rate_id>',
                  methods=['GET', 'POST'], endpoint="edit_ratedataset")
@login_required
def edit_rate(dataset_id, rate_id):
    rate = rateDataset_service.get_or_404(rate_id)
    if rate.user_id != current_user.id:
        flash('You are not authorized to edit this rate', 'error')
        return redirect(url_for('dataset.rate', dataset_id=dataset_id))
    form = RateForm(obj=rate)
    if form.validate_on_submit():
        result = rateDataset_service.update(
            rate_id,
            rate=form.rate.data,
            comment=form.comment.data,
            # user_id=current_user.id,
            # dataset_id=dataset_id
        )
        return rateDataset_service.handle_service_response2(
            result=result,
            errors=form.errors,
            success_url_redirect='dataset.rate',
            success_msg='Rate successfully published!',
            error_template='rate/create.html',
            form=form,
            id=dataset_id
        )
    return render_template('rate/edit.html', form=form, dataset=dataset_id, rate_id=rate_id)
@dataset_bp.route('/ratedataset/delete/<int:dataset_id>/<int:rate_id>',
                  methods=['POST'], endpoint="delete_ratedataset")
@login_required
def delete_rate(dataset_id, rate_id):
    rate = rateDataset_service.get_or_404(rate_id)
    if rate.user_id != current_user.id:
        flash('You are not authorized to delete this rate', 'error')
        return redirect(url_for('dataset.rate', dataset_id=dataset_id))
    result = rateDataset_service.delete(rate_id)
    if result:
        flash('Rate deleted successfully!', 'sucess')
    else:
        flash('Error deleting rate', 'error')
    return redirect(url_for('dataset.rate', dataset_id=dataset_id))

@dataset_bp.route("/dataset/download/<int:dataset_id>", methods=["GET"])
def download_dataset(dataset_id):
    dataset = dataset_service.get_or_404(dataset_id)

    file_path = f"uploads/user_{dataset.user_id}/dataset_{dataset.id}/"

    temp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(temp_dir, f"dataset_{dataset_id}.zip")

    with ZipFile(zip_path, "w") as zipf:
        for subdir, dirs, files in os.walk(file_path):
            for file in files:
                full_path = os.path.join(subdir, file)

                relative_path = os.path.relpath(full_path, file_path)

                zipf.write(
                    full_path,
                    arcname=os.path.join(
                        os.path.basename(zip_path[:-4]), relative_path
                    ),
                )

    user_cookie = request.cookies.get("download_cookie")
    if not user_cookie:
        user_cookie = str(
            uuid.uuid4()
        )  # Generate a new unique identifier if it does not exist
        # Save the cookie to the user's browser
        resp = make_response(
            send_from_directory(
                temp_dir,
                f"dataset_{dataset_id}.zip",
                as_attachment=True,
                mimetype="application/zip",
            )
        )
        resp.set_cookie("download_cookie", user_cookie)
    else:
        resp = send_from_directory(
            temp_dir,
            f"dataset_{dataset_id}.zip",
            as_attachment=True,
            mimetype="application/zip",
        )

    # Check if the download record already exists for this cookie
    existing_record = DSDownloadRecord.query.filter_by(
        user_id=current_user.id if current_user.is_authenticated else None,
        dataset_id=dataset_id,
        download_cookie=user_cookie
    ).first()

    if not existing_record:
        # Record the download in your database
        DSDownloadRecordService().create(
            user_id=current_user.id if current_user.is_authenticated else None,
            dataset_id=dataset_id,
            download_date=datetime.now(timezone.utc),
            download_cookie=user_cookie,
        )

    return resp


@dataset_bp.route("/doi/<path:doi>/", methods=["GET"])
def subdomain_index(doi):

    # Check if the DOI is an old DOI
    new_doi = doi_mapping_service.get_new_doi(doi)
    if new_doi:
        # Redirect to the same path with the new DOI
        return redirect(url_for('dataset.subdomain_index', doi=new_doi), code=302)

    # Try to search the dataset by the provided DOI (which should already be the new one)
    ds_meta_data = dsmetadata_service.filter_by_doi(doi)

    if not ds_meta_data:
        abort(404)

    # Get dataset
    dataset = ds_meta_data.data_set

    # Save the cookie to the user's browser
    user_cookie = ds_view_record_service.create_cookie(dataset=dataset)
    resp = make_response(render_template("dataset/view_dataset.html", dataset=dataset))
    resp.set_cookie("view_cookie", user_cookie)

    return resp


@dataset_bp.route("/dataset/unsynchronized/<int:dataset_id>/", methods=["GET"])
@login_required
def get_unsynchronized_dataset(dataset_id):

    # Get dataset
    dataset = dataset_service.get_unsynchronized_dataset(current_user.id, dataset_id)

    if not dataset:
        abort(404)

    return render_template("dataset/view_dataset.html", dataset=dataset)
