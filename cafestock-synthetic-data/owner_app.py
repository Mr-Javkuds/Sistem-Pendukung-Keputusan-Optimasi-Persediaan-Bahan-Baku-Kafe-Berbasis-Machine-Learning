"""Local owner application. Start: python owner_app.py --port 8765."""
from pathlib import Path
import argparse
import csv
import io
import json
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent
LOCK = threading.Lock()


def overview(branch):
    ingredients = pd.read_csv(ROOT / 'output/ingredients.csv')
    branches = pd.read_csv(ROOT / 'output/branches.csv')
    if branch not in branches.branch_id.values:
        raise ValueError('Cabang tidak ditemukan')
    recommendations = pd.read_csv(ROOT / 'prepared/10_optimization/owner_recommendations.csv')
    report = json.loads((ROOT / 'reports/optimization_report.json').read_text())
    metrics = json.loads((ROOT / 'reports/modeling_report.json').read_text())
    scores = pd.read_csv(ROOT / 'prepared/07_modeling/D_combined_RandomForest_test_predictions.csv')
    latest = scores[scores.branch_id.eq(branch)].sort_values('decision_at').groupby('ingredient_id').tail(1)
    rows = recommendations[recommendations.branch_id.eq(branch)].merge(
        ingredients[['ingredient_id', 'ingredient_name', 'unit', 'unit_cost_idr']], on='ingredient_id')
    # This score belongs to the historical policy on its recorded date, not the
    # counterfactual replay state used for the recommendation.
    risk_map = latest.set_index('ingredient_id').to_dict('index')
    records = []
    for row in rows.to_dict('records'):
        risk = risk_map.get(row['ingredient_id'])
        row['historical_risk_score'] = float(risk['risk_score']) if risk else None
        row['historical_risk_at'] = risk['decision_at'] if risk else None
        row['purchase_qty'] = row.pop('baseline_purchase_qty')
        row['estimated_cost_idr'] = row['purchase_qty'] * row['unit_cost_idr']
        row['reason'] = (f"Konsumsi/perkiraan {row['mean_daily_consumption_14d']:.1f} {row['unit']}/hari; "
            f"lead time {row['lead_time_days']} hari, masa simpan {row['shelf_life_days']} hari. "
            f"Stok {row['on_hand']:.1f}, pesanan berjalan {row['on_order']:.1f}; "
            f"kemasan {row['package_size']}, MOQ {row['minimum_order_qty']}.")
        records.append(row)
    approval_path = ROOT / 'local/approvals.json'
    with LOCK:
        approvals = json.loads(approval_path.read_text()) if approval_path.exists() else []
    return {'branches': branches[['branch_id', 'branch_name']].to_dict('records'),
        'recommendations': records, 'optimization': report, 'risk_threshold': metrics['primary_threshold'],
        'approvals': [a for a in approvals if a['branch_id'] == branch],
        'notice': 'Simulasi akademik • Data sintetis Semarang • Bukan stok langsung kafe nyata'}


class Handler(BaseHTTPRequestHandler):
    def send(self, code, body, content_type='application/json; charset=utf-8'):
        payload = body.encode('utf-8') if isinstance(body, str) else body
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        url = urlparse(self.path)
        try:
            if url.path == '/':
                return self.send(200, (ROOT / 'web/index.html').read_bytes(), 'text/html; charset=utf-8')
            if url.path == '/api/overview':
                branch = int(parse_qs(url.query).get('branch', ['1'])[0])
                return self.send(200, json.dumps(overview(branch), ensure_ascii=False, allow_nan=False))
            if url.path == '/api/export':
                branch = int(parse_qs(url.query).get('branch', ['1'])[0])
                rows = overview(branch)['recommendations']
                stream = io.StringIO()
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader(); writer.writerows(rows)
                return self.send(200, stream.getvalue(), 'text/csv; charset=utf-8')
            self.send(404, json.dumps({'error': 'Halaman tidak ditemukan'}))
        except (ValueError, KeyError) as error:
            self.send(400, json.dumps({'error': str(error)}))
        except FileNotFoundError:
            self.send(503, json.dumps({'error': 'Jalankan train_models.py lalu optimize_inventory.py terlebih dahulu.'}))

    def do_POST(self):
        try:
            # Reject cross-site browser submissions to this local app.
            host = self.headers.get('Host')
            origin = self.headers.get('Origin')
            if origin and origin != 'http://' + str(host):
                return self.send(403, json.dumps({'error': 'Origin ditolak'}))
            length = int(self.headers.get('Content-Length', '0'))
            if length <= 0 or length > 12000:
                raise ValueError('Ukuran permintaan tidak valid')
            data = json.loads(self.rfile.read(length))
            if self.path == '/api/sentiment':
                text = data.get('text', '')
                if not isinstance(text, str) or not text.strip() or len(text) > 4000:
                    raise ValueError('Isi teks 1–4000 karakter')
                model = joblib.load(ROOT / 'prepared/07_modeling/SVM.joblib')
                return self.send(200, json.dumps({'label': str(model.predict([text])[0]),
                    'notice': 'Model dilatih pada template sintetis; hasil teks nyata belum tervalidasi.'}))
            if self.path == '/api/approve':
                branch = int(data.get('branch_id', 0))
                state = overview(branch)
                item = {'branch_id': branch, 'recorded_at': datetime.now(timezone.utc).isoformat(),
                    'decision_at': state['recommendations'][0]['decision_at'],
                    'policy': state['optimization']['recommended_policy'],
                    'items': [{'ingredient_id': r['ingredient_id'], 'quantity': r['purchase_qty']}
                              for r in state['recommendations'] if r['purchase_qty'] > 0],
                    'status': 'approved_local_plan'}
                path = ROOT / 'local/approvals.json'
                with LOCK:
                    path.parent.mkdir(exist_ok=True)
                    previous = json.loads(path.read_text()) if path.exists() else []
                    identity = (branch, item['decision_at'], item['policy'])
                    if not any((a['branch_id'], a['decision_at'], a['policy']) == identity for a in previous):
                        previous.append(item)
                        temporary = path.with_suffix('.tmp')
                        temporary.write_text(json.dumps(previous, indent=2), encoding='utf-8')
                        temporary.replace(path)
                return self.send(200, json.dumps({'status': 'approved_local_plan',
                    'message': 'Persetujuan rencana tersimpan lokal. Tidak ada pesanan dikirim ke pemasok.'}))
            self.send(404, json.dumps({'error': 'Endpoint tidak ditemukan'}))
        except (ValueError, TypeError, KeyError) as error:
            self.send(400, json.dumps({'error': str(error)}))
        except FileNotFoundError:
            self.send(503, json.dumps({'error': 'Jalankan train_models.py lalu optimize_inventory.py terlebih dahulu.'}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'CafeStock: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
