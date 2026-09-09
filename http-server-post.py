#!/usr/bin/env python3
"""
HTTP-сервер для приёма файлов: каждый POST-файл сохраняется отдельно.

Эндпоинты:
    POST /любой_путь   — загрузка. Поддерживается:
        * multipart/form-data — один или несколько файлов в одном запросе
          (так отправляют браузеры и curl -F);
        * любой другой Content-Type — всё тело запроса считается одним файлом
          (имя берётся из заголовка X-File-Name, Content-Disposition или пути URL);
        * Transfer-Encoding: chunked.
    GET  /             — список сохранённых файлов (JSON).

Сохранение:
    * каталог uploads/ (создаётся автоматически);
    * имя файла санитизируется: нет ../, нет : * ? " < > | и управляющих символов;
    * если файл с таким именем уже есть — «имя (1).ext», «имя (2).ext», ...

Запуск:
    python3 upload_server.py [порт]      # порт по умолчанию 8000
"""

import json
import re
import sys
import uuid
from datetime import datetime
from email.parser import BytesParser
from email.policy import default as email_policy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = "0.0.0.0"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
UPLOAD_DIR = Path("uploads")
MAX_SIZE = 2 * 1024 ** 3            # 2 ГБ — страховочный лимит

UPLOAD_DIR.mkdir(exist_ok=True)


class PayloadTooLarge(Exception):
    pass


def safe_name(name: str) -> str:
    """Только базовое имя файла: без пути и опасных символов."""
    name = Path(name).name
    name = re.sub(r'[\\/:*?"<>|\x00-\x1f\x7f]', "_", name).strip()
    return name or "unnamed"


def fallback_name() -> str:
    """Сгенерированное имя, если клиент не прислал filename."""
    return "upload-{:%Y%m%d-%H%M%S}-{}".format(datetime.now(), uuid.uuid4().hex[:6])


def unique_path(name: str) -> Path:
    """Файл с таким именем уже есть -> «имя (1).ext», «имя (2).ext», ..."""
    path = UPLOAD_DIR / name
    if not path.exists():
        return path
    stem, suffix = path.stem, path.suffix
    for i in range(1, 10_000):
        path = UPLOAD_DIR / f"{stem} ({i}){suffix}"
        if not path.exists():
            return path
    raise FileExistsError("слишком много файлов с одинаковым именем")


class UploadHandler(BaseHTTPRequestHandler):
    server_version = "UploadServer/1.0"
    protocol_version = "HTTP/1.1"

    # ------------------------------------------------ тело запроса

    def _read_body(self) -> bytes:
        if "chunked" in (self.headers.get("Transfer-Encoding") or "").lower():
            chunks = []
            total = 0
            while True:
                line = self.rfile.readline().strip()
                size = int(line.split(b";")[0] or b"0", 16)
                if size == 0:
                    while True:                      # trailer-блок
                        trailer = self.rfile.readline()
                        if trailer in (b"\r\n", b"\n", b""):
                            break
                    break
                total += size
                if total > MAX_SIZE:
                    raise PayloadTooLarge(f"payload > {MAX_SIZE} bytes")
                chunks.append(self.rfile.read(size))
                self.rfile.readline()                # CRLF после чанка
            return b"".join(chunks)

        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise ValueError("некорректный Content-Length")
        if length > MAX_SIZE:
            raise PayloadTooLarge(f"payload {length} > {MAX_SIZE} bytes")
        return self.rfile.read(length) if length else b""

    # ------------------------------------------------ разбор файлов

    def _collect_files(self, body: bytes):
        """Возвращает [(field, filename, data)]. filename может быть ''."""
        ctype = self.headers.get("Content-Type") or ""
        files = []

        if ctype.lower().startswith("multipart/form-data"):
            # boundary в теле может быть в любом регистре — берём из заголовка как есть
            m = re.search(r'boundary="?([^";]+)"?', ctype)
            if not m:
                return files
            raw = f"Content-Type: {ctype}\r\n\r\n".encode() + body
            for part in BytesParser(policy=email_policy).parsebytes(raw).iter_parts():
                if part.get_content_disposition() != "form-data":
                    continue
                data = part.get_payload(decode=True)
                if data is None:
                    continue
                fname = part.get_param("filename", header="content-disposition")
                if fname is None:                    # обычное поле, не файл
                    continue
                field = part.get_param("name", header="content-disposition") or "file"
                files.append((field, fname, data))
        else:
            # всё тело запроса — один файл
            fname = self.headers.get("X-File-Name")
            if not fname:
                m = re.search(r'filename="?([^";]+)"?',
                              self.headers.get("Content-Disposition") or "")
                if m:
                    fname = m.group(1)
            if not fname:
                fname = self.path.rsplit("/", 1)[-1]
            files.append(("file", fname or "", body))

        return files

    # ------------------------------------------------ HTTP

    def _respond(self, code: int, obj) -> None:
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            body = self._read_body()
        except PayloadTooLarge as e:
            return self._respond(413, {"ok": False, "error": str(e)})
        except (ValueError, OSError) as e:
            return self._respond(400, {"ok": False, "error": f"bad request: {e}"})

        files = self._collect_files(body)
        if not files:
            return self._respond(400, {"ok": False, "error": "no files in request"})

        saved = []
        for field, fname, data in files:
            name = safe_name(fname) if fname else fallback_name()
            path = unique_path(name)
            path.write_bytes(data)
            saved.append({"field": field, "file": path.name, "size": len(data)})
            print(f"saved: {path}  ({len(data)} bytes)", flush=True)

        self._respond(200, {"ok": True, "files": saved})

    def do_GET(self):
        items = [
            {"file": p.name, "size": p.stat().st_size}
            for p in UPLOAD_DIR.iterdir() if p.is_file()
        ]
        items.sort(key=lambda x: x["file"])
        self._respond(200, {"count": len(items), "files": items})


def main():
    server = ThreadingHTTPServer((HOST, PORT), UploadHandler)
    print(f"upload server: http://{HOST}:{PORT}/  ->  {UPLOAD_DIR.resolve()}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopping...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
