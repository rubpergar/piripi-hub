from flask import jsonify
from app.modules.fakenodo import fakenodo_bp


@fakenodo_bp.route('', methods=["GET"])
def test_connection_fakenodo():
    response = {"status": "success", "message": "Connected to FakenodoAPI"}
    return jsonify(response)


@fakenodo_bp.route('/deposit/depositions', methods=['POST'])
def create_deposition():
    return jsonify({
        "id": 123456,
        "links": {
            "files": "/fakenodo/api/deposit/depositions/123456/files",
            "publish": "/fakenodo/api/deposit/depositions/123456/actions/publish"
        }
    }), 201


@fakenodo_bp.route('/deposit/depositions/<depositionId>', methods=["DELETE"])
def delete_deposition_fakenodo(depositionId):
    response = {
        "status": "success",
        "message": f"Deposition {depositionId} deleted",
    }
    return jsonify(response), 200


@fakenodo_bp.route('/deposit/depositions', methods=['GET'])
def get_all_depositions():
    fake_depositions = [
        {
            "id": 12345,
            "title": "Fake Deposition 1",
            "description": "Fake deposition",
            "creators": [{"name": "John Doe"}],
            "published": True
        },
        {
            "id": 67890,
            "title": "Fake Deposition 2",
            "description": "Fake deposition",
            "creators": [{"name": "Jane Smith"}],
            "published": False
        },
    ]
    return jsonify({"depositions": fake_depositions}), 200


@fakenodo_bp.route('/deposit/depositions/<int:deposition_id>/files', methods=['POST'])
def upload_file(deposition_id):
    return jsonify({
        "message": "File uploaded successfully"
    }), 201


@fakenodo_bp.route('/deposit/depositions/<int:deposition_id>/actions/publish', methods=['POST'])
def publish_deposition(deposition_id):
    return jsonify({
        "id": deposition_id,
        "doi": f"10.5072/fakenodo.{deposition_id}"
    }), 202


@fakenodo_bp.route('/deposit/depositions/<int:deposition_id>', methods=['GET'])
def get_deposition(deposition_id):
    return jsonify({
        "id": deposition_id,
        "metadata": {
            "title": "Sample Deposition",
            "upload_type": "publication",
            "publication_type": "article",
            "description": "Description",
        },
        "files": [
            {"filename": "file1.txt", "filesize": 1024},
            {"filename": "file2.pdf", "filesize": 2048}
        ],
        "published": True
    }), 200


@fakenodo_bp.route('/deposit/depositions/<int:deposition_id>/nonexistent', methods=['GET'])
def deposition_not_found(deposition_id):
    return jsonify({"message": "Deposition not found"}), 404