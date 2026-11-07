"""Local owner application. Start: python owner_app.py --port 8765."""
from pathlib import Path
import argparse
import csv
import io
import json
import math
import os
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import pandas as pd
from market_analysis import market_trend_analysis

ROOT = Path(__file__).resolve().parent
LOCK = threading.Lock()
SENTIMENT_LOCK = threading.Lock()
SENTIMENT_CHECKPOINT = Path(os.environ.get(
    'CAFESTOCK_INDOBERT_PATH', str(ROOT.parent / 'tmp/indobert-cafestock-fourclass')))
SENTIMENT_TOKENIZER = None
SENTIMENT_MODEL = None
SENTIMENT_TORCH = None


def load_sentiment_model():
    """Load the local fine-tuned IndoBERT checkpoint once when the server starts."""
    global SENTIMENT_TOKENIZER, SENTIMENT_MODEL, SENTIMENT_TORCH
    if not SENTIMENT_CHECKPOINT.is_dir():
        raise FileNotFoundError(
            f'Checkpoint IndoBERT tidak ditemukan: {SENTIMENT_CHECKPOINT}. '
            'Jalankan experiment_indobert.py terlebih dahulu.')
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification

    torch.set_num_threads(min(4, torch.get_num_threads()))
    SENTIMENT_TOKENIZER = AutoTokenizer.from_pretrained(SENTIMENT_CHECKPOINT)
    SENTIMENT_MODEL = AutoModelForSequenceClassification.from_pretrained(SENTIMENT_CHECKPOINT)
    SENTIMENT_MODEL.to(torch.device('cpu'))
    SENTIMENT_MODEL.eval()
    SENTIMENT_TORCH = torch


def predict_sentiment(text):
    if SENTIMENT_MODEL is None or SENTIMENT_TOKENIZER is None:
        raise RuntimeError('Model IndoBERT belum dimuat.')
    torch = SENTIMENT_TORCH
    encoded = SENTIMENT_TOKENIZER(text, truncation=True, padding='max_length',
                                  max_length=80, return_tensors='pt')
    with SENTIMENT_LOCK, torch.inference_mode():
        logits = SENTIMENT_MODEL(**encoded).logits[0]
        label_id = int(torch.argmax(logits).item())
    return str(SENTIMENT_MODEL.config.id2label[label_id])


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
        def quantity(value):
            return f"{value:,.1f}".rstrip('0').rstrip('.').replace(',', '_').replace('.', ',').replace('_', '.')

        # In the simulator's ML replay this stored rate is the forecast after
        # applying the selected safety factor; under baseline it is trailing usage.
        planned_daily_rate = float(row['mean_daily_consumption_14d'])
        policy = str(row.get('policy', 'baseline'))
        safety_factor = float(policy.removeprefix('ML_')) if policy.startswith('ML_') else 1.0
        forecast_daily_rate = planned_daily_rate / safety_factor if safety_factor else planned_daily_rate
        lead_days = int(row['lead_time_days'])
        reorder_days = lead_days + 1
        target_days = min(lead_days + 2, int(row['shelf_life_days']))
        stock_position = float(row['on_hand']) + float(row['on_order'])
        reorder_point = planned_daily_rate * reorder_days
        target_stock = planned_daily_rate * target_days
        needed_to_target = (max(0.0, target_stock - stock_position)
                            if stock_position < reorder_point else 0.0)
        computed_purchase = (max(float(row['minimum_order_qty']),
            math.ceil(needed_to_target / float(row['package_size'])) * float(row['package_size']))
            if needed_to_target > 0 else 0.0)
        row['purchase_explanation'] = {
            'policy': policy,
            'forecast_daily_rate': forecast_daily_rate,
            'safety_factor': safety_factor,
            'planned_daily_rate': planned_daily_rate,
            'lead_days': lead_days,
            'reorder_days': reorder_days,
            'target_days': target_days,
            'stock_position': stock_position,
            'reorder_point': reorder_point,
            'target_stock': target_stock,
            'needed_to_target': needed_to_target,
            'purchase_qty': float(row['purchase_qty']),
            'post_order_stock': stock_position + float(row['purchase_qty']),
            'package_size': float(row['package_size']),
            'minimum_order_qty': float(row['minimum_order_qty']),
        }
        unit = row['unit']
        if row['purchase_qty'] > 0:
            row['reason'] = (
                f"Ramalan kebutuhan {quantity(forecast_daily_rate)} {unit}/hari dengan faktor kebijakan "
                f"{quantity(safety_factor)} menghasilkan laju rencana {quantity(planned_daily_rate)} {unit}/hari. "
                f"Stok tersedia dan pesanan berjalan berjumlah {quantity(stock_position)} {unit}, di bawah "
                f"titik pemesanan {quantity(reorder_point)} {unit} untuk {reorder_days} hari kebutuhan. "
                f"Target {target_days} hari adalah {quantity(target_stock)} {unit}; kekurangan menuju target "
                f"{quantity(needed_to_target)} {unit}. Jumlah dibulatkan ke minimum/kemasan pemasok "
                f"{quantity(row['minimum_order_qty'])} {unit}, sehingga rencana beli {quantity(row['purchase_qty'])} {unit}. "
                f"Stok setelah pesanan tiba diperkirakan {quantity(row['purchase_explanation']['post_order_stock'])} {unit}; "
                f"estimasi anggaran Rp {quantity(row['estimated_cost_idr'])}.")
        else:
            row['reason'] = (
                f"Ramalan kebutuhan {quantity(forecast_daily_rate)} {unit}/hari dengan faktor kebijakan "
                f"{quantity(safety_factor)} menghasilkan titik pemesanan {quantity(reorder_point)} {unit}. "
                f"Posisi stok {quantity(stock_position)} {unit} masih memenuhi ambang pemesanan; belum perlu beli.")
        records.append(row)
    approval_path = ROOT / 'local/approvals.json'
    with LOCK:
        approvals = json.loads(approval_path.read_text()) if approval_path.exists() else []
    return {'branches': branches[['branch_id', 'branch_name']].to_dict('records'),
        'recommendations': records, 'optimization': report, 'risk_threshold': metrics['primary_threshold'],
        'approvals': [a for a in approvals if a['branch_id'] == branch]}


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
            if url.path == '/market_trends.js':
                return self.send(200, (ROOT / 'web/market_trends.js').read_bytes(), 'text/javascript; charset=utf-8')
            assets = {'/dashboard.js': ('dashboard.js', 'text/javascript'),
                      '/dashboard.css': ('dashboard.css', 'text/css'),
                      '/manrope-latin.woff2': ('manrope-latin.woff2', 'font/woff2'),
                      '/favicon.svg': ('favicon.svg', 'image/svg+xml')}
            if url.path in assets:
                name, kind = assets[url.path]
                return self.send(200, (ROOT/'web'/name).read_bytes(), kind+'; charset=utf-8')
            if url.path == '/api/overview':
                branch = int(parse_qs(url.query).get('branch', ['1'])[0])
                return self.send(200, json.dumps(overview(branch), ensure_ascii=False, allow_nan=False))
            if url.path == '/api/trends':
                query = parse_qs(url.query)
                branch = int(query.get('branch', ['1'])[0])
                weeks = int(query.get('weeks', ['12'])[0])
                return self.send(200, json.dumps(market_trend_analysis(ROOT, branch, weeks),
                    ensure_ascii=False, allow_nan=False))
            if url.path == '/api/export':
                branch = int(parse_qs(url.query).get('branch', ['1'])[0])
                rows = overview(branch)['recommendations']
                stream = io.StringIO()
                writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
                writer.writeheader(); writer.writerows(rows)
                return self.send(200, stream.getvalue(), 'text/csv; charset=utf-8')
            if not url.path.startswith('/api/'):
                return self.send(404, (ROOT / 'web/not-found.html').read_bytes(), 'text/html; charset=utf-8')
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
                label = predict_sentiment(text)
                return self.send(200, json.dumps({'label': label, 'model': 'IndoBERT'}))
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
    load_sentiment_model()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'CafeStock: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
