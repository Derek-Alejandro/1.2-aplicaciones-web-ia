import json
import os

from http.server import BaseHTTPRequestHandler
from openai import OpenAI


# Lee ALLOWED_ORIGIN desde las variables de entorno de Vercel
# Ejemplo:
# https://derek-alejandro.github.io
ALLOWED_ORIGIN = (
    os.environ
    .get("ALLOWED_ORIGIN", "")
    .strip()
    .rstrip("/")
)


class handler(BaseHTTPRequestHandler):

    def add_cors_headers(self):
        origin = (
            self.headers
            .get("Origin", "")
            .strip()
            .rstrip("/")
        )

        # Si ALLOWED_ORIGIN está configurado,
        # solamente permite ese origen
        if ALLOWED_ORIGIN:
            if origin == ALLOWED_ORIGIN:
                self.send_header(
                    "Access-Control-Allow-Origin",
                    origin
                )
                self.send_header(
                    "Vary",
                    "Origin"
                )

        # Útil para pruebas locales si no se configuró
        # ALLOWED_ORIGIN
        else:
            self.send_header(
                "Access-Control-Allow-Origin",
                "*"
            )


    def send_json(self, status_code, data):
        body = json.dumps(
            data,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status_code)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.add_cors_headers()

        self.send_header(
            "Content-Length",
            str(len(body))
        )

        self.end_headers()

        self.wfile.write(body)


    def do_OPTIONS(self):
        origin = (
            self.headers
            .get("Origin", "")
            .strip()
            .rstrip("/")
        )

        # Verifica que el origen esté permitido
        if ALLOWED_ORIGIN and origin != ALLOWED_ORIGIN:
            self.send_response(403)
            self.end_headers()
            return

        self.send_response(204)

        self.add_cors_headers()

        self.send_header(
            "Access-Control-Allow-Methods",
            "POST, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

        self.send_header(
            "Access-Control-Max-Age",
            "86400"
        )

        self.end_headers()


    def do_GET(self):
        self.send_json(
            405,
            {
                "error":
                    "Este endpoint solamente acepta POST."
            }
        )


    def do_POST(self):
        try:

            # -----------------------------
            # Verificar origen
            # -----------------------------

            origin = (
                self.headers
                .get("Origin", "")
                .strip()
                .rstrip("/")
            )

            if ALLOWED_ORIGIN and origin != ALLOWED_ORIGIN:
                self.send_json(
                    403,
                    {
                        "error":
                            "Origen no autorizado."
                    }
                )
                return


            # -----------------------------
            # Leer tamaño del contenido
            # -----------------------------

            content_length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )

            if content_length <= 0:
                self.send_json(
                    400,
                    {
                        "error":
                            "La petición está vacía."
                    }
                )
                return

            if content_length > 5000:
                self.send_json(
                    413,
                    {
                        "error":
                            "La petición es demasiado grande."
                    }
                )
                return


            # -----------------------------
            # Leer JSON
            # -----------------------------

            body = self.rfile.read(
                content_length
            )

            data = json.loads(
                body.decode("utf-8")
            )


            # -----------------------------
            # Obtener mensaje
            # -----------------------------

            message = str(
                data.get(
                    "message",
                    ""
                )
            ).strip()

            if not message:
                self.send_json(
                    400,
                    {
                        "error":
                            "Es necesario escribir un mensaje."
                    }
                )
                return

            if len(message) > 1000:
                self.send_json(
                    400,
                    {
                        "error":
                            "El mensaje supera los 1000 caracteres."
                    }
                )
                return


            # -----------------------------
            # Obtener API Key
            # -----------------------------

            api_key = os.environ.get(
                "OPENAI_API_KEY"
            )

            if not api_key:
                self.send_json(
                    500,
                    {
                        "error":
                            "OPENAI_API_KEY no está configurada."
                    }
                )
                return


            # -----------------------------
            # Crear cliente OpenAI
            # -----------------------------

            client = OpenAI(
                api_key=api_key
            )


            # -----------------------------
            # Consultar modelo
            # -----------------------------

            response = client.chat.completions.create(
                model="gpt-4o-mini",

                messages=[
                    {
                        "role": "system",
                        "content":
                            "Eres un asistente educativo "
                            "especializado en Tecnologías de "
                            "Información y Comunicaciones. "
                            "Responde siempre en español, "
                            "de manera clara, breve y didáctica."
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],

                max_tokens=500
            )


            # -----------------------------
            # Obtener respuesta
            # -----------------------------

            reply = (
                response
                .choices[0]
                .message
                .content
            )


            # -----------------------------
            # Responder al frontend
            # -----------------------------

            self.send_json(
                200,
                {
                    "reply": reply
                }
            )


        # -----------------------------
        # JSON incorrecto
        # -----------------------------

        except json.JSONDecodeError:

            self.send_json(
                400,
                {
                    "error":
                        "El cuerpo no contiene JSON válido."
                }
            )


        # -----------------------------
        # Cualquier otro error
        # -----------------------------

        except Exception as error:

            print(
                f"Error en /api/chat: "
                f"{type(error).__name__}: "
                f"{error}"
            )

            self.send_json(
                500,
                {
                    "error":
                        "No fue posible consultar el modelo de IA."
                }
            )