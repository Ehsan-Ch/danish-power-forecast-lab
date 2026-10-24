import argparse
def main():
    p=argparse.ArgumentParser(description='Nordcast research workbench');sub=p.add_subparsers(dest='cmd',required=True)
    sub.add_parser('download').add_argument('--data',default='data')
    r=sub.add_parser('backtest');r.add_argument('--data',default='data');r.add_argument('--out',default='reports/custom/run')
    sub.add_parser('serve').add_argument('--port',type=int,default=8789)
    a=p.parse_args()
    if a.cmd=='download':
        from .data import download
        download(a.data)
    elif a.cmd=='backtest':
        from .pipeline import run
        run(a.data,a.out)
    else:
        from .server import serve
        serve(a.port)
if __name__=='__main__':main()
