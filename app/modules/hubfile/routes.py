from datetime import datetime, timezone
import os
import uuid
import zipfile
import io
from flask import current_app, jsonify, make_response, request, send_from_directory, send_file
from flask_login import current_user
from app.modules.hubfile import hubfile_bp
from app.modules.hubfile.models import HubfileDownloadRecord, HubfileViewRecord
from app.modules.hubfile.services import HubfileDownloadRecordService, HubfileService

from app import db


@hubfile_bp.route("/file/download/<int:file_id>", methods=["GET"])
def download_file(file_id):
    file = HubfileService().get_or_404(file_id)
    filename = file.name

    directory_path = f"uploads/user_{file.feature_model.data_set.user_id}/dataset_{file.feature_model.data_set_id}/"
    parent_directory_path = os.path.dirname(current_app.root_path)
    file_path = os.path.join(parent_directory_path, directory_path)

    # Get the cookie from the request or generate a new one if it does not exist
    user_cookie = request.cookies.get("file_download_cookie")
    if not user_cookie:
        user_cookie = str(uuid.uuid4())

    # Check if the download record already exists for this cookie
    existing_record = HubfileDownloadRecord.query.filter_by(
        user_id=current_user.id if current_user.is_authenticated else None,
        file_id=file_id,
        download_cookie=user_cookie
    ).first()

    if not existing_record:
        # Record the download in your database
        HubfileDownloadRecordService().create(
            user_id=current_user.id if current_user.is_authenticated else None,
            file_id=file_id,
            download_date=datetime.now(timezone.utc),
            download_cookie=user_cookie,
        )

    # Save the cookie to the user's browser
    resp = make_response(
        send_from_directory(directory=file_path, path=filename, as_attachment=True)
    )
    resp.set_cookie("file_download_cookie", user_cookie)

    return resp


@hubfile_bp.route('/file/view/<int:file_id>', methods=['GET'])
def view_file(file_id):
    file = HubfileService().get_or_404(file_id)
    filename = file.name

    directory_path = f"uploads/user_{file.feature_model.data_set.user_id}/dataset_{file.feature_model.data_set_id}/"
    parent_directory_path = os.path.dirname(current_app.root_path)
    file_path = os.path.join(parent_directory_path, directory_path, filename)

    try:
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read()

            user_cookie = request.cookies.get('view_cookie')
            if not user_cookie:
                user_cookie = str(uuid.uuid4())

            # Check if the view record already exists for this cookie
            existing_record = HubfileViewRecord.query.filter_by(
                user_id=current_user.id if current_user.is_authenticated else None,
                file_id=file_id,
                view_cookie=user_cookie
            ).first()

            if not existing_record:
                # Register file view
                new_view_record = HubfileViewRecord(
                    user_id=current_user.id if current_user.is_authenticated else None,
                    file_id=file_id,
                    view_date=datetime.now(),
                    view_cookie=user_cookie
                )
                db.session.add(new_view_record)
                db.session.commit()

            # Prepare response
            response = jsonify({'success': True, 'content': content})
            if not request.cookies.get('view_cookie'):
                response = make_response(response)
                response.set_cookie('view_cookie', user_cookie, max_age=60*60*24*365*2)

            return response
        else:
            return jsonify({'success': False, 'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@hubfile_bp.route("/dataset/download_selected", methods=["GET"])
def download_selected_files():
    # IDs modelos de la URL
    file_ids_param = request.args.get('file_ids')
    if not file_ids_param:
        return jsonify({'success': False, 'error': 'No file IDs provided'}), 400

    # Lista IDs modelos
    try:
        file_ids = [int(file_id.strip()) for file_id in file_ids_param.split(',')]
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid file IDs format'}), 400

    # Crear un stream de bytes para el archivo ZIP
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file_id in file_ids:
            file = HubfileService().get_or_404(file_id)
            filename = file.name
                     
            directory_path = f"uploads/user_{file.feature_model.data_set.user_id}/dataset_{file.feature_model.data_set_id}/"
            parent_directory_path = os.path.dirname(current_app.root_path)
            file_path = os.path.join(parent_directory_path, directory_path, filename)

            zip_file.write(file_path, arcname=filename)  # Añadir el archivo al ZIP

            # Get the cookie from the request or generate a new one if it does not exist
            user_cookie = request.cookies.get("file_download_cookie")
            if not user_cookie:
                user_cookie = str(uuid.uuid4())
                
            # Check if the download record already exists for this cookie
            existing_record = HubfileDownloadRecord.query.filter_by(
                user_id=current_user.id if current_user.is_authenticated else None,
                file_id=file_id,
                download_cookie=user_cookie
            ).first()

            if not existing_record:
                # Record the download in your database
                HubfileDownloadRecordService().create(
                    user_id=current_user.id if current_user.is_authenticated else None,
                    file_id=file_id,
                    download_date=datetime.now(timezone.utc),
                    download_cookie=user_cookie,
                )

    file_id_str = "_".join(str(file_id) for file_id in file_ids)
    zip_filename = f"models_{file_id_str}.zip"

    # Preparar la respuesta con el archivo ZIP
    zip_buffer.seek(0)
    response = make_response(send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name=zip_filename
    ))
    response.set_cookie("file_download_cookie", user_cookie)

    return response
