from flask import jsonify, send_file, request
from . import fakenodo_bp
import tempfile
import os

datasets = {}
dataset_counter = 0

# Upload all files from dataset
@fakenodo_bp.route('/fakenodo/upload', methods=['POST'])
def upload_dataset():
    file = request.files['file']
    if file:
        global dataset_counter
        dataset_id = dataset_counter
        dataset_counter += 1
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, file.filename)
        file.save(file_path)
        datasets[dataset_id] = {
            'id': dataset_id,
            'filename': file.filename,
            'file_path': file_path
        }
        return jsonify({'id': dataset_id, 'filename': file.filename}), 201
    return jsonify({'error': 'No file uploaded'}), 400


# Get dataset info
@fakenodo_bp.route('/fakenodo/info/<dataset_id>', methods=['GET'])
def get_Dataset(dataset_id):
    dataset = datasets.get(dataset_id)
    if dataset:
        return send_file(dataset['file_path'], as_attachment=True, download_name=dataset['filename'])
    return jsonify({'error': 'Dataset not found'}), 404


# Get All
@fakenodo_bp.route('/fakenodo/datasets', methods=['GET'])
def list_datasets():
    return jsonify(list(datasets.values()))


# Delete a deposition
@fakenodo_bp.route('/fakenodo/dataset/<int:dataset_id>', methods=['DELETE'])
def delete_dataset(dataset_id):
    dataset = datasets.pop(dataset_id, None)
    if dataset:
        os.remove(dataset['file_path'])
        return jsonify({'message': 'Dataset deleted'}), 200
    return jsonify({'error': 'Dataset not found'}), 404