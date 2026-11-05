"""Render EDA from an audited JSON summary; no fitting or model evaluation."""
import argparse
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def render(summary_path,output_dir):
    summary=json.loads(Path(summary_path).read_text(encoding='utf-8'))
    output_dir=Path(output_dir); output_dir.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes=plt.subplots(2,3,figsize=(16,9),layout='constrained')
    sentiment=summary['train_sentiment_labels']
    axes[0,0].bar(list(sentiment),list(sentiment.values()),color='#287c87')
    axes[0,0].set(title='Sentimen train yang eligible',ylabel='Jumlah teks unik')
    risk=summary['train_risk_labels']
    axes[0,1].bar(['Tidak stockout','Stockout'],[risk.get('0',0),risk.get('1',0)],color=['#287c87','#cb6745'])
    axes[0,1].set(title='Target risiko pada train',ylabel='Jumlah keputusan')
    menu=summary['train_product_units']
    axes[0,2].barh(list(menu),list(menu.values()),color='#287c87')
    axes[0,2].set(title='Unit terjual per menu pada train',xlabel='Fulfilled product units')
    daily=summary['train_daily_sales']
    axes[1,0].plot(range(len(daily)),list(daily.values()),color='#287c87',linewidth=1)
    axes[1,0].set(title='Penjualan harian pada train',xlabel='Urutan hari train',ylabel='Fulfilled product units')
    monthly=summary['train_social_batches']
    axes[1,1].bar(range(len(monthly)),list(monthly.values()),color='#287c87')
    axes[1,1].set_xticks(range(len(monthly)),list(monthly),rotation=45,ha='right')
    axes[1,1].set(title='Batch sosial train (termasuk duplikat mentah)',ylabel='Jumlah postingan')
    availability=summary['train_social_availability']
    axes[1,2].bar(['Belum ada batch','Batch tersedia'],[availability.get('0',0),availability.get('1',0)],color=['#cb6745','#287c87'])
    axes[1,2].set(title='Ketersediaan fitur sosial pada train',ylabel='Jumlah keputusan')
    fig.suptitle('EDA CafeStock Semarang — data sintetis; distribusi target memakai train saja',fontsize=15)
    fig.savefig(output_dir/'eda_train_overview.png',dpi=150)
    plt.close(fig)
    return {'python':__import__('sys').version,'matplotlib':matplotlib.__version__}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('summary'); p.add_argument('output_dir'); args=p.parse_args()
    print(json.dumps(render(args.summary,args.output_dir)))
