"""Make a conservative byte-level diff of two Fuji backup files.

This does not decode Fuji's proprietary backup format or claim property-level
readback. It records only offsets and printable runs, which is safe evidence
for deciding whether a later controlled decode is possible.
"""
from pathlib import Path
import argparse, json, hashlib, re

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('before',type=Path); ap.add_argument('after',type=Path); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    x,y=a.before.read_bytes(),a.after.read_bytes()
    if len(x)!=len(y): raise SystemExit('backup sizes differ; refusing offset diff')
    changed=[i for i,(u,v) in enumerate(zip(x,y)) if u!=v]
    runs=[]
    for m in re.finditer(rb'[ -~]{4,}',y): runs.append({'offset':m.start(),'text':m.group().decode('ascii','replace')})
    out={'kind':'fuji-backup-byte-diff-v1','before':str(a.before),'after':str(a.after),'before_sha256':sha(a.before),'after_sha256':sha(a.after),'size_bytes':len(x),'changed_byte_count':len(changed),'changed_offsets':changed,'after_printable_runs':runs,'property_level_decoded':False,'warning':'Byte offsets and printable strings are not Fuji property names. No write or property-level readback is inferred.'}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,indent=2)+'\n'); print(json.dumps(out,indent=2))
if __name__=='__main__': main()
