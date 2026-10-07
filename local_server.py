"""Local-only web server and Ollama bridge for the AutomiaIA prototype."""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OLLAMA = "http://127.0.0.1:11434"
MODEL = "qwen3:1.7b"


def ollama_request(path: str, payload: dict | None = None) -> dict:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        OLLAMA + path,
        data=data,
        headers={"Content-Type": "application/json"} if data else {},
        method="POST" if data else "GET",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.loads(response.read().decode("utf-8"))


def ensure_ollama():
    try:
        ollama_request("/api/tags")
        return
    except (OSError, urllib.error.URLError):
        pass

    executable = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
    if executable.is_file():
        subprocess.Popen(
            [str(executable), "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        for _ in range(20):
            time.sleep(0.5)
            try:
                ollama_request("/api/tags")
                return
            except (OSError, urllib.error.URLError):
                continue


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_json(self, status: int, value: dict):
        encoded = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        if self.path == "/api/status":
            try:
                models = ollama_request("/api/tags").get("models", [])
                names = [model.get("name", "") for model in models]
                self.send_json(200, {"ollama": True, "models": names, "modelReady": any(name == MODEL or name.startswith(MODEL + ":") for name in names)})
            except (OSError, urllib.error.URLError, json.JSONDecodeError):
                self.send_json(200, {"ollama": False, "models": [], "modelReady": False})
            return
        super().do_GET()

    def do_POST(self):
        if self.path != "/api/chat":
            self.send_json(404, {"error": "Rota não encontrada."})
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size > 64_000:
                self.send_json(413, {"error": "Mensagem grande demais."})
                return
            incoming = json.loads(self.rfile.read(size).decode("utf-8"))
            model = incoming.get("model", MODEL)
            if model != MODEL:
                self.send_json(400, {"error": "Modelo não permitido para esta demonstração."})
                return
            info = incoming.get("businessInfo", {})
            context = (
                "Você é o atendente virtual de demonstração da AutomiaIA. Responda em português brasileiro, "
                "com simpatia, clareza e poucas frases. Considere o cadastro abaixo como fonte única e responda "
                "com os mesmos nomes, valores, dias e horários que estão nele. Não altere nem arredonde preços, "
                "não invente endereço, forma de pagamento, política ou disponibilidade. Se a informação não "
                "estiver cadastrada ou a pergunta estiver ambígua, diga que vai confirmar com a equipe. Faça "
                "uma pergunta de cada vez. Nunca diga que marcou, reservou ou confirmou um horário: esta "
                "demonstração não está conectada a uma agenda real. Para pedidos de agendamento, colete apenas "
                "dia e período desejado e explique que a equipe precisa confirmar. Para clínica, não dê diagnóstico, "
                "indique remédios nem avalie urgências; encaminhe a pessoa para um profissional de saúde. Para "
                "oficina, não afirme o custo final de um reparo sem avaliação.\n\n"
                + json.dumps(info, ensure_ascii=False)
            )
            messages = [{"role": "system", "content": context}]
            messages.extend(incoming.get("messages", [])[-12:])
            result = ollama_request(
                "/api/chat",
                {
                    "model": MODEL,
                    "messages": messages,
                    "stream": False,
                    "think": False,
                    "options": {"temperature": 0.4, "num_predict": 160},
                },
            )
            self.send_json(200, result)
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            message = "Modelo não encontrado. Abra o terminal e execute: ollama pull qwen3:1.7b" if error.code == 404 else detail
            self.send_json(503, {"error": message})
        except (OSError, urllib.error.URLError, TimeoutError):
            self.send_json(503, {"error": "O Ollama não respondeu. Confira se o aplicativo está aberto."})
        except (ValueError, json.JSONDecodeError):
            self.send_json(400, {"error": "Não consegui ler a mensagem enviada."})

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))


if __name__ == "__main__":
    ensure_ollama()
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("AutomiaIA local: http://127.0.0.1:8000")
    print("Este protótipo aceita conexões somente deste computador. Feche esta janela para parar.")
    if os.environ.get("AUTOMIAIA_NO_BROWSER") != "1":
        threading.Timer(1, lambda: webbrowser.open("http://127.0.0.1:8000")).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Encerrando o servidor local...")
    finally:
        server.server_close()
