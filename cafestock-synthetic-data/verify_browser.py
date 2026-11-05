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
        for branch in ('2', '3', '1'):
            with page.expect_response(lambda r: '/api/overview?branch='+branch in r.url) as response:
                page.select_option('#branch', branch)
            assert response.value.ok
            page.wait_for_function("!document.querySelector('#approve').disabled")
            assert page.locator('#rows tr').count() == 10
            assert 'branch='+branch in page.locator('#export').get_attribute('href')
        page.locator('#rows details').first.click()
        page.fill('#text', 'Matchanya enak tetapi harganya mahal.')
        page.click('#analyze')
        page.wait_for_function("document.querySelector('#sentiment').textContent.startsWith('Hasil:')")
        with page.expect_download() as downloaded:
            page.click('#export')
        assert 'purchase_qty' in Path(downloaded.value.path()).read_text()
        page.screenshot(path=str(out/'desktop.png'), full_page=True)
        page.set_viewport_size({'width': 390, 'height': 844})
        page.screenshot(path=str(out/'mobile.png'), full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
        assert not errors, errors
        (out/'browser_check.json').write_text(json.dumps({'browser': 'headless Chrome',
            'checks': ['page load', 'three branches', '10 ingredient rows', 'sentiment inference',
                       'CSV download', 'mobile no page overflow', 'no JavaScript errors'],
            'source_sha256': {name: hashlib.sha256((out.parents[1]/name).read_bytes()).hexdigest()
                              for name in ('owner_app.py', 'web/index.html')},
            'passed': True}, indent=2), encoding='utf-8')
        print('PASS: Chrome UI flows and desktop/mobile screenshots')
        browser.close()


if __name__ == '__main__':
    run()
