"""实时运行日志服务：把洛雪容器的 docker logs 流式转给网页。

只监听 127.0.0.1:8793，由 nginx 反代到 /runtime/。
只读、只暴露最近的日志行，不提供任何执行能力。
"""
import hmac
import json
import os
import queue
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CONTAINER = os.getenv('LUOXUE_CONTAINER', 'luoxue-astrbot')
PORT = int(os.getenv('LUOXUE_LOG_PORT', '8793'))
PASSWORD_FILE = os.path.join(os.environ.get('LUOXUE_HOME', os.getcwd()), 'room_admin_password')
BUFFER = 400

buf = []
buf_lock = threading.Lock()
subscribers = []


def password():
    try:
        with open(PASSWORD_FILE, encoding='utf-8') as handle:
            return handle.read().strip()
    except Exception:
        return ''


def pump():
    """后台跑 docker logs -f，把每行放进环形缓冲 + 分发给订阅者。"""
    while True:
        try:
            proc = subprocess.Popen(
                ['docker', 'logs', '--tail', '200', '-f', CONTAINER],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1,
                text=True, encoding='utf-8', errors='replace')
            for line in proc.stdout:
                line = line.rstrip('\n')
                with buf_lock:
                    buf.append(line)
                    if len(buf) > BUFFER:
                        del buf[:len(buf) - BUFFER]
                    for q in list(subscribers):
                        try:
                            q.put_nowait(line)
                        except Exception:
                            pass
            proc.wait(timeout=5)
        except Exception:
            time.sleep(3)


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *args):
        pass

    def _json(self, payload, code=200):
        body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def _ok(self):
        expected = password()
        supplied = self.headers.get('X-Password') or ''
        return bool(expected) and hmac.compare_digest(supplied.encode('utf-8'), expected.encode('utf-8'))

    def do_GET(self):
        if not self._ok():
            self._json({'ok': False, 'error': 'password'}, 403)
            return
        if self.path.startswith('/logs'):
            with buf_lock:
                lines = list(buf)[-300:]
            self._json({'ok': True, 'lines': lines, 'running': True})
            return
        if self.path.startswith('/stream'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('X-Accel-Buffering', 'no')
            self.end_headers()
            q = queue.Queue(maxsize=500)
            subscribers.append(q)
            try:
                with buf_lock:
                    backlog = list(buf)[-120:]
                for line in backlog:
                    self.wfile.write(('data: ' + json.dumps(line, ensure_ascii=False) + '\n\n').encode())
                    self.wfile.flush()
                last_ping = time.time()
                while True:
                    try:
                        line = q.get(timeout=1)
                        self.wfile.write(('data: ' + json.dumps(line, ensure_ascii=False) + '\n\n').encode())
                        self.wfile.flush()
                    except queue.Empty:
                        if time.time() - last_ping > 15:
                            self.wfile.write(b': ping\n\n')
                            self.wfile.flush()
                            last_ping = time.time()
            except Exception:
                pass
            finally:
                try:
                    subscribers.remove(q)
                except Exception:
                    pass
            return
        self._json({'ok': False, 'error': 'not found'}, 404)


if __name__ == '__main__':
    threading.Thread(target=pump, daemon=True).start()
    print('logs api on 127.0.0.1:%d' % PORT, flush=True)
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
