from flask import Flask, request, jsonify
from flasgger import Swagger
import json
import os

NOTES_FILE = os.getenv("NOTES_PATH", "/data/notes.json")

def create_app():
    app = Flask(__name__)

    app.config["SWAGGER"] = {"title": "Notes API v3.0.0"}

    # Swagger/Flasgger template with simple definitions
    template = {
        "swagger": "2.0",
        "info": {"title": "Notes API", "version": "3.0.0"},
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

    def load_notes():
        """Cargar notas desde el archivo de volumen persistente"""
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
        """Agregar una nota al archivo de volumen persistente"""
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
        with open(NOTES_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def save_notes(notes: list):
        """Guardar todas las notas reescribiendo el archivo completo"""
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(NOTES_FILE), exist_ok=True)
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            for note in notes:
                f.write(json.dumps(note, ensure_ascii=False) + "\n")

    def delete_note_by_title(title: str) -> bool:
        """Eliminar una nota por título. Retorna True si se eliminó, False si no se encontró"""
        notes = load_notes()
        original_count = len(notes)
        
        # Filtrar notas que no tengan el título especificado
        notes = [note for note in notes if note.get("title") != title]
        
        if len(notes) < original_count:
            save_notes(notes)
            return True
        return False

    @app.route('/', methods=['GET'])
    def root():
        """Endpoint raíz - Mensaje indicando que el API está activo.

        ---
        tags:
          - Status
        responses:
          200:
            description: Mensaje de confirmación que el API está activo
            schema:
              $ref: '#/definitions/Message'
        """
        return jsonify({"message": "API de Notas v3.0.0 está activo"}), 200

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
        """Información de versión y entorno para blue-green deployment.

        ---
        tags:
          - Info
        responses:
          200:
            description: Información de versión y entorno
            schema:
              type: object
              properties:
                version:
                  type: string
                  example: v3.0.0
                environment:
                  type: string
                  example: blue
                hostname:
                  type: string
                deployment_type:
                  type: string
                  example: blue-green
        """
        import socket
        hostname = socket.gethostname()
        
        # Detectar entorno basado en hostname o variable de entorno
        environment = os.getenv("DEPLOYMENT_ENV", "unknown")
        if "blue" in hostname.lower():
            environment = "blue"
        elif "green" in hostname.lower():
            environment = "green"
        
        return jsonify({
            "version": "v3.0.0",
            "environment": environment,
            "hostname": hostname,
            "deployment_type": "blue-green",
            "features": ["create", "read", "delete", "version-switching"],
            "status": "ready"
        }), 200

    @app.route("/add/<title>", methods=["POST"])
    def add_note(title):
        """Agregar una nueva nota.

        ---
        tags:
          - Notes
        parameters:
          - name: title
            in: path
            type: string
            required: true
            description: Título para la nota
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
                  description: Contenido de la nota
        responses:
          201:
            description: Nota creada exitosamente
            schema:
              $ref: '#/definitions/Message'
          400:
            description: Cuerpo de petición inválido o faltante
            schema:
              $ref: '#/definitions/Message'
        """
        data = request.get_json()
        note = (data or {}).get("note")
        if not note:
            return jsonify({"message": "El campo 'note' es requerido en el cuerpo JSON"}), 400

        entry = {"title": title, "note": note}
        append_note(entry)

        return jsonify({"message": f"Nota '{title}' agregada exitosamente"}), 201

    @app.route('/list', methods=['GET'])
    def get_notes():
        """Lista todas las notas guardadas.

        ---
        tags:
          - Notes
        responses:
          200:
            description: Lista de notas
            schema:
              type: array
              items:
                $ref: '#/definitions/Note'
          404:
            description: No se encontraron notas
            schema:
              $ref: '#/definitions/Message'
        """
        notes = load_notes()
        if not notes:
            return jsonify({"message": "No se encontraron notas"}), 404
        return jsonify(notes), 200

    @app.route('/delete/<title>', methods=['DELETE'])
    def delete_note(title):
        """Eliminar una nota por título.

        ---
        tags:
          - Notes
        parameters:
          - name: title
            in: path
            type: string
            required: true
            description: Título de la nota a eliminar
        responses:
          200:
            description: Nota eliminada exitosamente
            schema:
              $ref: '#/definitions/Message'
          404:
            description: Nota no encontrada
            schema:
              $ref: '#/definitions/Message'
        """
        if delete_note_by_title(title):
            return jsonify({"message": f"Nota '{title}' eliminada exitosamente"}), 200
        else:
            return jsonify({"message": f"Nota '{title}' no encontrada"}), 404

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)
