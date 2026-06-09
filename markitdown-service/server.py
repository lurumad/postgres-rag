from flask import Flask, request, jsonify
from markitdown import MarkItDown
import tempfile, os

app = Flask(__name__)
md = MarkItDown()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/convert", methods=["POST"])
def convert():
    if request.is_json and "path" in request.json:
        path = request.json["path"]
        if not os.path.exists(path):
            return jsonify({"error": f"File not found: {path}"}), 404
        result = md.convert(path)
        return jsonify({"markdown": result.text_content})

    if "file" in request.files:
        f = request.files["file"]
        suffix = os.path.splitext(f.filename)[1] if f.filename else ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            f.save(tmp.name)
            tmp_path = tmp.name
        try:
            result = md.convert(tmp_path)
            return jsonify({"markdown": result.text_content})
        finally:
            os.unlink(tmp_path)

    return jsonify({"error": "Provide 'path' (JSON) or 'file' (multipart)"}), 400

@app.route("/delete", methods=["POST"])
def delete():
    path = request.json.get("path")
    if not path or not os.path.exists(path):
        return jsonify({"error": "File not found"}), 404
    os.remove(path)
    return jsonify({"deleted": path})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)