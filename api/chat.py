import json
import os
from http.server import BaseHTTPRequestHandler
from openai import OpenAI

# Lee la variable de entorno y limpia espacios o barras finales
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "").strip().rstrip("/")

class handler(BaseHTTPRequestHandler):

    def add_cors_headers(self):
        origin = self.headers.get("Origin", "")
        # Si no hay ALLOWED_ORIGIN definido o coincide exactamente con el origen
        if not ALLOWED_ORIGIN or origin.strip().rstrip("/") == ALLOWED_ORIGIN:
            self.send_header("Access-Control-Allow-Origin", origin if origin else "*")
            self.send_header("Vary", "Origin")

    def send_json(self, status_code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.add_cors_headers()
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        # Responder 204 siempre enviando las cabeceras CORS
        self.send_response(204)
        self.add_cors_headers()
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self):
        self.send_json(405, {"error": "Este endpoint solamente acepta POST."})

    def do_POST(self):
        try:
            origin = self.headers.get("Origin", "")

            if ALLOWED_ORIGIN and origin.strip().rstrip("/") != ALLOWED_ORIGIN:
                self.send_json(403, {"error": "Origen no autorizado."})
                return

            content_length = int(self.headers.get("Content-Length", 0))

            if content_length <= 0 or content_length > 5000:
                self.send_json(413, {"error": "Petición no válida o demasiado grande."})
                return

            body = self.rfile.read(content_length)
            data = json.loads(body.decode("utf-8"))
            message = str(data.get("message", "")).strip()

            if not message:
                self.send_json(400, {"error": "Es necesario escribir un mensaje."})
                return

            if len(message) > 1000:
                self.send_json(400, {"error": "El mensaje supera los 1000 caracteres."})
                return

            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                self.send_json(500, {"error": "OPENAI_API_KEY no está configurada."})
                return

            client = OpenAI(api_key=api_key)

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente educativo especializado en Tecnologías de Información y Comunicaciones. Responde siempre en español, de manera clara, breve y didáctica."
                    },
                    {"role": "user", "content": message}
                ],
                max_tokens=500
            )

            self.send_json(200, {"reply": response.choices[0].message.content})

        except json.JSONDecodeError:
            self.send_json(400, {"error": "El cuerpo no contiene JSON válido."})
        except Exception as error:
            print(f"Error en /api/chat: {type(error)._name_}: {error}")
            self.send_json(500, {"error": "No fue posible consultar el modelo de IA."})