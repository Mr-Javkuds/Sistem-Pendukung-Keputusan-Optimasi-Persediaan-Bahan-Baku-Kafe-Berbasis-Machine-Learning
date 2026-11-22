"""Real checkpoint and Chrome smoke test for the three dashboard model adapters."""
from pathlib import Path
import argparse
import json
from playwright.sync_api import sync_playwright


def run():
    parser=argparse.ArgumentParser();parser.add_argument('--base-url',default='http://127.0.0.1:8765')
    args=parser.parse_args()
    out=Path(__file__).resolve().parent/'reports/app/three_models';out.mkdir(parents=True,exist_ok=True)
    results={};errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1100})
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(args.base_url+'/?view=evaluation',wait_until='networkidle',timeout=60000)
        page.wait_for_function("!document.querySelector('#sentiment-model').disabled")
        options=page.request.get(args.base_url+'/api/sentiment/options').json()
        assert all(options[k] for k in ['indobert_available','laya_product_available','laya_trend_available']),options
        assert page.locator('#sentiment-model option').all_text_contents()==['IndoBERT','Laya Sentimen Produk','Laya Tren Sentimen']
        assert not page.locator('#trend-sentiment-context').is_visible()
        for model,task in [('indobert','product_sentiment'),('laya_product','product_sentiment'),('laya_trend','menu_interest')]:
            page.select_option('#sentiment-model',model)
            page.fill('#text','Rasanya enak.')
            if model=='laya_trend':
                assert page.locator('#trend-sentiment-context').is_visible()
                page.click('#analyze');assert page.locator('#sentiment-target').get_attribute('aria-invalid')=='true'
                page.fill('#sentiment-target','Es Matcha Latte')
                page.click('#analyze');assert page.locator('#sentiment-caption').get_attribute('aria-invalid')=='true'
                page.fill('#sentiment-caption','Unggahan yang memperkenalkan varian Es Matcha Latte baru.')
            with page.expect_response(lambda r:r.url.endswith('/api/sentiment'),timeout=240000) as response:
                page.click('#analyze')
            assert response.value.ok,response.value.text()
            data=response.value.json();assert data['task']==task
            assert data['label'] in ['positive','negative','neutral','mixed']
            page.wait_for_function("!document.querySelector('#analyze').disabled")
            text=page.locator('#sentiment').inner_text()
            assert data['model'] in text
            if model=='laya_trend':
                payload=response.value.request.post_data_json
                assert payload['target_product']=='Es Matcha Latte' and payload['parent_caption']
                label={'positive':'Tertarik mencoba','negative':'Tidak tertarik','neutral':'Arah ketertarikan belum jelas','mixed':'Tertarik tetapi ragu/menolak'}[data['label']]
                assert label in text
            results[model]={'response':data,'display':text}
            print(model,json.dumps(data,ensure_ascii=True),flush=True)
        panel=page.locator('section[aria-labelledby="sentiment-heading"]')
        panel.screenshot(path=str(out/'desktop.png'))
        page.set_viewport_size({'width':390,'height':844})
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        assert page.locator('#sentiment-target').evaluate('e=>getComputedStyle(e).fontSize')=='16px'
        panel.screenshot(path=str(out/'mobile.png'))
        page.select_option('#sentiment-model','laya_product')
        assert not page.locator('#trend-sentiment-context').is_visible()
        assert page.locator('#sentiment-target').is_disabled()
        with page.expect_response(lambda r:r.url.endswith('/api/sentiment')) as response:page.click('#analyze')
        assert set(response.value.request.post_data_json)=={'text','model'}
        assert response.value.ok
        assert not errors,errors
        browser.close()
    (out/'browser_check.json').write_text(json.dumps({'models':results,'options':options,'js_errors':errors,
        'mobile_no_overflow':True,'context_validation':True,'product_context_hidden':True},indent=2,ensure_ascii=False),encoding='utf-8')
    print('Three real models and responsive browser checks passed.',flush=True)


if __name__=='__main__':run()
