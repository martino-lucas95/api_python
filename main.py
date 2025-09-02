from flask import Flask, request, jsonify, send_from_directory
from flasgger import Swagger
import json
import os
from datetime import datetime, timezone
import uuid

NOTES_FILE = os.getenv("NOTES_PATH", "/data/notes.json")

def create_app():
    app = Flask(__name__)
    app.config["SWAGGER"] = {"title": "Notes API"}

    # Swagger/Flasgger template with simple definitions
    template = {
        "swagger": "2.0",
        "info": {"title": "Notes API", "version": "0.0.1"},
        "basePath": "/",
        "schemes": ["http"],
        "consumes": ["application/json"],
        "produces": ["application/json"],
        "definitions": {
            "Note": {
                "type": "object",
                "required": ["title", "note"],
                "properties": {
                    "title": {"type": "string"},
                    "note": {"type": "string"}
                }
            },
            "Message": {
                "type": "object",
                "properties": {"message": {"type": "string"}}
            }
        }
    }

    Swagger(app, template=template, config={
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec_1",
            "route": "/apispec_1.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
    })

    def _utc_now_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat() + "Z"

    def load_notes():
        if not os.path.exists(NOTES_FILE):
            return []
        notes = []
        with open(NOTES_FILE, 'r', encoding='utf-8') as n:
            for line in n:
                line = line.strip()
                if not line:
                    continue
                try:
                    notes.append(json.loads(line))
                except Exception:
                    # Skip malformed lines
                    continue
        return notes

    def append_note(entry: dict):
        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def to_v1(entry: dict) -> dict:
        return {
            "title": entry.get("title"),
            "note": entry.get("note")
        }

    def to_v2(entry: dict) -> dict:
        # Build a stable id if not present (from title+note)
        entry_id = entry.get("id") or str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{entry.get('title','')}::{entry.get('note','')}"))
        created_at = entry.get("created_at")
        updated_at = entry.get("updated_at")
        return {
            "id": entry_id,
            "title": entry.get("title"),
            "content": entry.get("note"),
            "tags": entry.get("tags", []),
            "archived": bool(entry.get("archived", False)),
            "created_at": created_at,
            "updated_at": updated_at,
        }

    @app.route('/', methods=['GET'])
    def healthy():
        """Health check endpoint.

        ---
        tags:
          - Health
        responses:
          200:
            description: API liveness status
            schema:
              type: object
              properties:
                status:
                  type: string
                  example: ok
        """
        return jsonify({"status": "ok"}), 200

    @app.route('/healthz', methods=['GET'])
    def healthz():
        """Kubernetes probe endpoint.

        ---
        tags:
          - Health
        responses:
          200:
            description: API health probe
        """
        return jsonify({"status": "ok"}), 200

    @app.route('/version', methods=['GET'])
    def version_info():
        """Version and environment information.

        ---
        tags:
          - Health
        responses:
          200:
            description: Version and environment info
        """
        import socket
        hostname = socket.gethostname()
        
        # Detect environment based on hostname or env vars
        environment = "unknown"
        if "blue" in hostname.lower():
            environment = "blue"
        elif "green" in hostname.lower():
            environment = "green"
        
        # Try to get from environment variable as fallback
        environment = os.getenv("DEPLOYMENT_ENV", environment)
        
        version = "v2.0.0"
        if environment == "blue":
            version = "v2.0.0"  # Blue is stable version
        elif environment == "green":
            version = "v3.0.0"  # Green is new version
            
        return jsonify({
            "version": version,
            "environment": environment,
            "hostname": hostname,
            "has_patch_bug": version in ["v2.0.0", "v3.0.0"],
            "status": "ok"
        }), 200

    @app.route("/add/<title>", methods=["POST"])
    def add_note(title):
        """Add a new note.

        ---
        tags:
          - Notes
        parameters:
          - name: title
            in: path
            type: string
            required: true
            description: Title for the note entry
          - in: body
            name: body
            required: true
            schema:
              type: object
              required:
                - note
              properties:
                note:
                  type: string
        responses:
          201:
            description: Note created
            schema:
              $ref: '#/definitions/Message'
          400:
            description: Missing or invalid body
            schema:
              $ref: '#/definitions/Message'
        """
        data = request.get_json()
        note = (data or {}).get("note")
        if not note:
            return jsonify({"message": "Field 'note' is required in JSON body"}), 400

        entry = {"title": title, "note": note}
        append_note(entry)

        return jsonify({"message": f"Note '{title}' added successfully"}), 201

    @app.route('/list', methods=['GET'])
    def get_notes():
        """List all saved notes.

        ---
        tags:
          - Notes
        responses:
          200:
            description: List of notes
            schema:
              type: array
              items:
                $ref: '#/definitions/Note'
          404:
            description: No notes found
            schema:
              $ref: '#/definitions/Message'
        """
        notes = load_notes()
        if not notes:
            return jsonify({"message": "No notes found"}), 404
        return jsonify(notes), 200

    @app.route('/api/v1/notes', methods=['GET'])
    def v1_list_notes():
        """List notes (v1 schema).

        ---
        tags:
          - Notes v1
        responses:
          200:
            description: List of notes (v1)
            schema:
              type: array
              items:
                $ref: '#/definitions/Note'
          404:
            description: No notes found
            schema:
              $ref: '#/definitions/Message'
        """
        notes = load_notes()
        if not notes:
            return jsonify({"message": "No notes found"}), 404
        return jsonify([to_v1(n) for n in notes]), 200

    @app.route('/api/v1/notes', methods=['POST'])
    def v1_create_note():
        """Create note (v1 schema).

        ---
        tags:
          - Notes v1
        parameters:
          - in: body
            name: body
            required: true
            schema:
              $ref: '#/definitions/Note'
        responses:
          201:
            description: Note created
            schema:
              $ref: '#/definitions/Message'
          400:
            description: Missing fields
            schema:
              $ref: '#/definitions/Message'
        """
        data = request.get_json() or {}
        title = data.get("title")
        note = data.get("note")
        if not title or not note:
            return jsonify({"message": "Fields 'title' and 'note' are required"}), 400
        entry = {"title": title, "note": note}
        append_note(entry)
        return jsonify({"message": f"Note '{title}' added successfully"}), 201

    @app.route('/api/v2/notes', methods=['GET'])
    def v2_list_notes():
        """List notes (v2 schema with metadata).

        ---
        tags:
          - Notes v2
        responses:
          200:
            description: List of notes (v2)
            schema:
              type: array
              items:
                type: object
        """
        notes = load_notes()
        if not notes:
            return jsonify([]), 200
        return jsonify([to_v2(n) for n in notes]), 200

    @app.route('/api/v2/notes', methods=['POST'])
    def v2_create_note():
        """Create note (v2 schema with metadata).

        ---
        tags:
          - Notes v2
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              required: [title, content]
              properties:
                title:
                  type: string
                content:
                  type: string
                tags:
                  type: array
                  items:
                    type: string
                archived:
                  type: boolean
        responses:
          201:
            description: Note created (v2)
            schema:
              type: object
          400:
            description: Missing fields
            schema:
              $ref: '#/definitions/Message'
        """
        data = request.get_json() or {}
        title = data.get("title")
        content = data.get("content") or data.get("note")
        if not title or not content:
            return jsonify({"message": "Fields 'title' and 'content' are required"}), 400
        now = _utc_now_iso()
        entry = {
            "id": str(uuid.uuid4()),
            "title": title,
            "note": content,
            "tags": data.get("tags", []),
            "archived": bool(data.get("archived", False)),
            "created_at": now,
            "updated_at": now,
        }
        append_note(entry)
        return jsonify(to_v2(entry)), 201

    @app.route('/api/v2/notes/<note_id>', methods=['PATCH'])
    def v2_update_note(note_id):
        """Update note (v2 schema) - WITH INTENTIONAL BUG.

        ---
        tags:
          - Notes v2
        parameters:
          - name: note_id
            in: path
            type: string
            required: true
          - in: body
            name: body
            schema:
              type: object
              properties:
                title:
                  type: string
                content:
                  type: string
                tags:
                  type: array
                  items:
                    type: string
                archived:
                  type: boolean
        responses:
          200:
            description: Note updated
          404:
            description: Note not found
          500:
            description: Server error (BUG!)
        """
        # INTENTIONAL BUG: Always return 500 error
        return jsonify({"error": "Internal server error - PATCH is broken!"}), 500

    # ===== API v3 (NEW FUNCTIONALITY FOR GREEN) =====
    @app.route('/api/v3/notes', methods=['GET'])
    def v3_list_notes():
        """List notes with enhanced metadata (v3).
        
        ---
        tags:
          - Notes v3
        responses:
          200:
            description: List of notes with enhanced metadata (v3)
            schema:
              type: object
              properties:
                version:
                  type: string
                  example: "v3"
                count:
                  type: integer
                  example: 5
                notes:
                  type: array
                  items:
                    type: object
                    properties:
                      id:
                        type: integer
                      title:
                        type: string
                      note:
                        type: string
                      editable:
                        type: boolean
        """
        notes = load_notes()
        enhanced_notes = []
        for i, note in enumerate(notes):
            enhanced_notes.append({
                "id": i + 1,
                "title": note.get("title", ""),
                "note": note.get("note", ""),
                "editable": True  # v3 feature: all notes are editable
            })
        
        return jsonify({
            "version": "v3",
            "count": len(enhanced_notes),
            "notes": enhanced_notes,
            "features": ["create", "edit", "delete"]
        }), 200

    @app.route('/api/v3/notes', methods=['POST'])
    def v3_create_note():
        """Create a note (v3) with enhanced validation.
        
        ---
        tags:
          - Notes v3
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                title:
                  type: string
                  minLength: 1
                  maxLength: 100
                note:
                  type: string
                  minLength: 1
        responses:
          201:
            description: Note created successfully
          400:
            description: Validation error
        """
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400
            
        title = data.get("title", "").strip()
        note = data.get("note", "").strip()
        
        # Enhanced validation
        if not title or len(title) > 100:
            return jsonify({"error": "Title must be 1-100 characters"}), 400
        if not note:
            return jsonify({"error": "Note content is required"}), 400
            
        entry = {"title": title, "note": note}
        append_note(entry)
        
        notes = load_notes()
        note_id = len(notes)
        
        return jsonify({
            "message": "Note created successfully",
            "id": note_id,
            "title": title
        }), 201

    @app.route('/api/v3/notes/<int:note_id>', methods=['PUT'])
    def v3_update_note(note_id):
        """Update a note completely (v3) - NEW EDIT FEATURE!
        
        ---
        tags:
          - Notes v3
        parameters:
          - in: path
            name: note_id
            type: integer
            required: true
            description: The ID of the note to update (1-based)
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                title:
                  type: string
                note:
                  type: string
        responses:
          200:
            description: Note updated successfully
          400:
            description: Validation error
          404:
            description: Note not found
        """
        notes = load_notes()
        if note_id < 1 or note_id > len(notes):
            return jsonify({"error": "Note not found"}), 404
            
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON body required"}), 400
            
        title = data.get("title", "").strip()
        note_content = data.get("note", "").strip()
        
        if not title:
            return jsonify({"error": "Title is required"}), 400
        if not note_content:
            return jsonify({"error": "Note content is required"}), 400
            
        # Update the note
        notes[note_id - 1] = {"title": title, "note": note_content}
        save_notes(notes)
        
        return jsonify({
            "message": "Note updated successfully",
            "id": note_id,
            "title": title
        }), 200

    @app.route('/api/v3/notes/<int:note_id>', methods=['DELETE'])
    def v3_delete_note(note_id):
        """Delete a note (v3) - NEW DELETE FEATURE!
        
        ---
        tags:
          - Notes v3
        parameters:
          - in: path
            name: note_id
            type: integer
            required: true
            description: The ID of the note to delete (1-based)
        responses:
          200:
            description: Note deleted successfully
          404:
            description: Note not found
        """
        notes = load_notes()
        if note_id < 1 or note_id > len(notes):
            return jsonify({"error": "Note not found"}), 404
            
        deleted_note = notes[note_id - 1]
        del notes[note_id - 1]
        save_notes(notes)
        
        return jsonify({
            "message": "Note deleted successfully",
            "deleted_title": deleted_note.get("title", "")
        }), 200

    @app.route('/ui')
    def frontend():
        """Modern frontend interface."""
        return send_from_directory('static', 'index.html')
    
    @app.route('/static/<path:filename>')
    def static_files(filename):
        """Serve static files."""
        return send_from_directory('static', filename)

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)
