"""Optional Chrome UI smoke test: run while owner_app.py is serving locally."""
from pathlib import Path
import argparse
import json
import hashlib
from playwright.sync_api import sync_playwright


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8765')
    args = parser.parse_args()
    out = Path(__file__).resolve().parent/'reports/app'
    out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chrome', headless=True)
        page = browser.new_page(viewport={'width': 1440, 'height': 1100}, device_scale_factor=1)
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(args.base_url, wait_until='networkidle')
        page.wait_for_function("document.querySelectorAll('#rows tr').length===10")
        page.wait_for_function("document.querySelectorAll('#trend-values tr').length===12")
        assert page.locator('#trend-heading').is_visible()
        assert page.locator('#trend-chart polyline').count() == 4
        assert page.locator('#trend-comparisons tr').count() == 6
        page.uncheck('#series-sales_units')
        page.uncheck('#series-stock_value_idr')
        assert page.locator('#trend-chart polyline').count() == 2
        assert page.locator('#trend-comparisons tr').count() == 1
        page.check('#series-sales_units')
        page.check('#series-stock_value_idr')
        page.select_option('#trend-scale', 'original')
        assert int(page.locator('#trend-chart').get_attribute('viewBox').split()[-1]) > 900
        page.select_option('#trend-scale', 'compare')
        page.select_option('#trend-category', '2')
        page.select_option('#trend-period', '52')
        page.wait_for_function("document.querySelectorAll('#trend-values tr').length===52")
        assert len(page.locator('#trend-chart polyline[data-series="interest_index"]').get_attribute('points').split()) == 52
        for branch in ('2', '3', '1'):
            with page.expect_response(lambda r: '/api/overview?branch='+branch in r.url) as response:
                page.select_option('#branch', branch)
            assert response.value.ok
            page.wait_for_function("!document.querySelector('#approve').disabled")
            assert page.locator('#rows tr').count() == 10
            assert 'branch='+branch in page.locator('#export').get_attribute('href')
            assert page.locator('.stock-chart').count() == 10
            assert page.locator('.stock-chart svg').count() == 10
            assert page.locator('.chart-legend li').count() == 40
            assert page.locator('.stock-chart svg path').count() == 20
            # Each purchase graph exposes the projected stock, reorder threshold, target, and delivery.
            assert page.evaluate('''async () => {
                const data = await (await fetch('/api/overview?branch='+document.querySelector('#branch').value)).json();
                return data.recommendations.every((r,i) => {
                    const chart = document.querySelectorAll('#rows tr')[i].querySelector('.stock-chart');
                    const e = r.purchase_explanation;
                    return !!e && chart.querySelectorAll('path').length === 2
                        && chart.querySelectorAll('.chart-legend li').length === 4
                        && e.post_order_stock === e.stock_position + e.purchase_qty
                        && e.target_days >= e.lead_days;
                });
            }''')
        # Query state survives reload and the task navigation remains keyboard friendly.
        page.reload(wait_until='networkidle')
        page.wait_for_function("document.querySelectorAll('#trend-values tr').length===52")
        assert page.locator('#trend-category').input_value() == '2'
        page.keyboard.press('Tab')
        assert page.locator('.skip-link').evaluate('(element)=>element===document.activeElement')
        page.locator('nav [data-route="purchase"]').click()
        assert page.locator('#purchase-heading').is_visible()
        assert 'view=purchase' in page.url
        page.check('#purchase-only')
        assert page.locator('#rows .buy').count() == page.locator('#rows tr').count()
        page.uncheck('#purchase-only')
        page.locator('#rows summary').first.click()
        page.locator('#rows tr').filter(has=page.locator('.buy')).first.locator('summary').click()
        assert page.locator('details[open] .business-reason').count() == 2
        assert page.locator('details[open] h3').first.inner_text() == 'Dasar rekomendasi'
        page.locator('nav [data-route="evaluation"]').click()
        page.click('#analyze')
        assert page.locator('#text').get_attribute('aria-invalid') == 'true'
        assert page.locator('#text').evaluate('(element)=>element===document.activeElement')
        page.fill('#text', 'Matchanya enak tetapi harganya mahal.')
        page.click('#analyze')
        page.wait_for_function("document.querySelector('#sentiment').textContent.startsWith('Hasil IndoBERT:')")
        assert 'undefined' not in page.locator('#sentiment').inner_text()
        for phrase in ('sintetis', 'belum tervalidasi', 'belum diuji', 'probabilitas terkalibrasi'):
            assert phrase not in page.locator('body').inner_text().lower()
        with page.expect_download() as downloaded:
            page.click('#export')
        assert 'purchase_qty' in Path(downloaded.value.path()).read_text()
        page.locator('nav [data-route="analysis"]').click()
        page.route('**/api/trends?*', lambda route: route.fulfill(status=503, json={'error':'temporary'}), times=1)
        page.select_option('#trend-period','4')
        page.locator('#retry-trends').wait_for(state='visible')
        assert page.locator('#trend-comparisons tr').count() == 0
        page.click('#retry-trends')
        page.wait_for_function("document.querySelectorAll('#trend-values tr').length===4")
        page.select_option('#trend-period','12')
        page.wait_for_function("document.querySelectorAll('#trend-values tr').length===12")
        page.screenshot(path=str(out/'desktop.png'), full_page=True)
        page.set_viewport_size({'width': 768, 'height': 1024})
        page.screenshot(path=str(out/'tablet.png'), full_page=True)
        page.set_viewport_size({'width': 390, 'height': 844})
        page.screenshot(path=str(out/'mobile.png'), full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        assert not errors, errors
        (out/'browser_check.json').write_text(json.dumps({'browser': 'headless Chrome',
            'checks': ['page load', 'three branches', '10 ingredient rows', '10 SVG stock projections',
                       'projected stock with/without purchase', 'reorder and target reference lines',
                       'policy math included in explanation', 'requested notices removed', 'IndoBERT sentiment inference',
                       'CSV download', 'four aligned comparison series', 'two-series toggle and pair comparison',
                       'original-unit panels', 'trend category and 52-week selection',
                       'task navigation', 'persisted URL filters', 'keyboard skip link',
                       'purchase-only filter', 'inline text validation', 'trend error and retry',
                       'mobile no page overflow', 'no JavaScript errors'],
            'source_sha256': {name: hashlib.sha256((out.parents[1]/name).read_bytes()).hexdigest()
                              for name in ('owner_app.py', 'market_analysis.py', 'web/index.html',
                                           'web/dashboard.css', 'web/dashboard.js', 'web/market_trends.js')},
            'passed': True}, indent=2), encoding='utf-8')
        print('PASS: Chrome UI flows and desktop/mobile screenshots')
        browser.close()


if __name__ == '__main__':
    run()
