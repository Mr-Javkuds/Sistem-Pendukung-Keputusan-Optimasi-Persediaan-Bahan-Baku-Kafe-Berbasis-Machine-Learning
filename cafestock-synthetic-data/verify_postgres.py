"""Import and reject invalid writes in a disposable cluster, never an existing DB."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile
import json
import pandas as pd
from pglast import parse_sql

def run():
    root=Path(__file__).resolve().parent
    parser=argparse.ArgumentParser()
    parser.add_argument('--pg-bin',type=Path,default=Path('C:/Program Files/PostgreSQL/18/bin'))
    parser.add_argument('--port',type=int,default=55440)
    args=parser.parse_args()
    commands=[]
    def command(program,*arguments,cwd=None):
        invocation=[str(args.pg_bin/(program+('.exe' if __import__('os').name=='nt' else ''))),*map(str,arguments)]
        # Windows server children may inherit PIPE handles, keeping communicate()
        # waiting after pg_ctl exits. An ordinary file has no EOF dependency.
        with tempfile.TemporaryFile(mode='w+',encoding='utf-8') as log:
            result=subprocess.run(invocation,cwd=cwd,stdout=log,stderr=log,stdin=subprocess.DEVNULL)
            log.seek(0); output=log.read()
        commands.append((program,result.returncode,output))
        if result.returncode: raise RuntimeError(commands[-1][2])
        return output
    parse_sql((root/'sql'/'schema.sql').read_text(encoding='utf-8'))
    temp=Path(tempfile.mkdtemp(prefix='cafestock-pg-'))
    data=temp/'cluster'; started=False
    try:
        command('initdb','-D',data,'-U','cafestock_test','--auth=trust','--encoding=UTF8','--locale=C')
        command('pg_ctl','-D',data,'-l',temp/'server.log','-o',f'-p {args.port} -h 127.0.0.1','-w','start')
        started=True
        connect=['-h','127.0.0.1','-p',args.port,'-U','cafestock_test','-d','postgres','-v','ON_ERROR_STOP=1']
        command('psql',*connect,'-f','sql/schema.sql','-f','sql/import.sql','-f','sql/constraint_checks.sql',cwd=root)
        expected={p.stem:len(pd.read_csv(p)) for p in (root/'output').glob('*.csv')}
        for table,n in expected.items():
            actual=command('psql',*connect,'-At','-c',f'SELECT count(*) FROM {table};').strip()
            if int(actual)!=n: raise AssertionError((table,n,actual))
        version=command('psql',*connect,'-At','-c','SELECT version();').strip()
        (root/'reports'/'postgres_verification.md').write_text(
            '# PostgreSQL verification\n\nPASS: schema parsed, all CSV tables imported in a fresh disposable cluster; '
            'all database row counts equal CSV row counts.\n\n'+version+'\n\n'
            'Six negative cases rejected: duplicate PK, orphan FK, negative package, overfulfilled item, '
            'inventory conservation violation, deletion of referenced ingredient. Each case was rolled back '
            'in a subtransaction. SQL import uses explicit columns, UTF-8 and NULL empty fields.\n\n'
            '```json\n'+json.dumps(expected,indent=2)+'\n```\n',encoding='utf-8')
        print(f'PASS: imported {len(expected)} tables and rejected six invalid mutations')
    finally:
        if started: command('pg_ctl','-D',data,'-m','fast','-w','stop')
        # Deliberately retain the isolated temp directory for diagnostic inspection.
        print('Stopped disposable cluster; diagnostic directory:',temp)

if __name__=='__main__': run()
