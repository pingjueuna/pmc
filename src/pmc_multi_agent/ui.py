from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict

from .execution import ExecutionRunner
from .workflow import default_blueprint


def run_payload(actual_wrong_rate: Dict[str, float] | None = None) -> Dict[str, object]:
    runner = ExecutionRunner()
    payload, stages = runner.run_with_stages(
        default_blueprint(),
        actual_wrong_rate or {"PM-001": 0.51, "PM-002": 0.44, "PM-003": 0.63},
    )
    payload["stages"] = stages
    return payload


HTML = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>PMC Multi-Agent 실행 대시보드</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 2rem; }
    h1 { margin-top: 0; }
    .row { display: flex; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap; }
    input { padding: .5rem; min-width: 140px; }
    button { padding: .5rem .8rem; cursor: pointer; }
    table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
    th, td { border: 1px solid #ddd; padding: .5rem; text-align: left; }
    pre { background: #111; color: #eee; padding: 1rem; overflow: auto; border-radius: 8px; }
  </style>
</head>
<body>
  <h1>PM 역량인증 멀티 에이전트 실행 화면</h1>
  <p>오답률 입력 후 실행하면 단계별 실행 시간과 결과를 즉시 확인할 수 있습니다.</p>

  <div class="row">
    <input id="pm1" value="0.51" />
    <input id="pm2" value="0.44" />
    <input id="pm3" value="0.63" />
    <button onclick="runPipeline()">실행</button>
  </div>

  <h3>Stage 실행 결과</h3>
  <table id="stageTable">
    <thead><tr><th>Stage</th><th>Duration (ms)</th><th>Metrics</th></tr></thead>
    <tbody></tbody>
  </table>

  <h3>원본 JSON</h3>
  <pre id="raw"></pre>

  <script>
    async function runPipeline() {
      const actual = {
        'PM-001': Number(document.getElementById('pm1').value),
        'PM-002': Number(document.getElementById('pm2').value),
        'PM-003': Number(document.getElementById('pm3').value),
      };
      const res = await fetch('/api/run', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({actual})
      });
      const data = await res.json();

      const tbody = document.querySelector('#stageTable tbody');
      tbody.innerHTML = '';
      for (const stage of data.stages) {
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${stage.name}</td><td>${stage.duration_ms}</td><td>${JSON.stringify(stage.metrics)}</td>`;
        tbody.appendChild(tr);
      }
      document.getElementById('raw').textContent = JSON.stringify(data, null, 2);
    }

    runPipeline();
  </script>
</body>
</html>
"""


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path != "/":
            self.send_error(404, "Not found")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode("utf-8"))

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/api/run":
            self.send_error(404, "Not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        body = json.loads(raw)
        actual = body.get("actual")
        payload = run_payload(actual)

        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003
        return


def serve_dashboard(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    print(f"Dashboard running on http://{host}:{port}")
    server.serve_forever()
