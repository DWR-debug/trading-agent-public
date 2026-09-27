"""Q043 fixed fresh-disjoint coverage preflight wrapper."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from automation.coverage_preflight import main as coverage_main

def run(preregistration:Path, output_root:Path)->None:
    import sys
    sys.argv=["coverage_preflight","--preregistration",str(preregistration),"--output-root",str(output_root)]
    coverage_main()

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--preregistration",required=True)
    p.add_argument("--output-root",required=True)
    a=p.parse_args()
    run(Path(a.preregistration),Path(a.output_root))
