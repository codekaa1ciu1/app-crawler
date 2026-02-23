"""Flask web portal for viewing and managing crawler paths."""
import os
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_crawler.database import CrawlerDatabase


app = Flask(__name__)
CORS(app)

# Initialize database
# Use project root crawler_paths.db so running from web_portal works
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(project_root, 'crawler_paths.db')
db = CrawlerDatabase(db_path)


@app.route('/')
def index():
    """Main page - list all paths."""
    return render_template('index.html')


@app.route('/api/paths', methods=['GET'])
def get_paths():
    """Get all crawler paths."""
    paths = db.get_all_paths()
    return jsonify(paths)


@app.route('/api/paths/<path_id>', methods=['GET'])
def get_path(path_id):
    """Get specific path details."""
    path = db.get_path_by_id(path_id)
    if not path:
        return jsonify({"error": "Path not found"}), 404
    
    steps = db.get_path_steps(path_id)
    interventions = db.get_human_interventions(path_id)
    
    return jsonify({
        "path": path,
        "steps": steps,
        "interventions": interventions
    })


@app.route('/api/paths/<path_id>', methods=['PUT'])
def update_path(path_id):
    """Update path metadata."""
    data = request.json
    
    success = db.update_path(
        path_id=path_id,
        name=data.get('name'),
        description=data.get('description')
    )
    
    if success:
        return jsonify({"message": "Path updated successfully"})
    else:
        return jsonify({"error": "Path not found"}), 404


@app.route('/api/paths/<path_id>', methods=['DELETE'])
def delete_path(path_id):
    """Delete a path."""
    success = db.delete_path(path_id)
    
    if success:
        return jsonify({"message": "Path deleted successfully"})
    else:
        return jsonify({"error": "Path not found"}), 404


@app.route('/api/paths/<path_id>/close', methods=['POST'])
def close_path(path_id):
    """Close an active path (set is_active=0)."""
    success = db.set_path_active(path_id, False)
    
    if success:
        return jsonify({"message": "Path closed successfully"})
    else:
        return jsonify({"error": "Path not found"}), 404


@app.route('/api/paths/<path_id>/steps', methods=['GET'])
def get_path_steps(path_id):
    """Get all steps for a path."""
    steps = db.get_path_steps(path_id)
    return jsonify(steps)


@app.route('/screenshots/<path:filename>')
def serve_screenshot(filename):
    """Serve screenshot files."""
    screenshots_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'screenshots')
    return send_from_directory(screenshots_dir, filename)


if __name__ == '__main__':
    import os
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5050)
