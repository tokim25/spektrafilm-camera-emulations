"""z30-lightroom command line."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="z30-lightroom", description="Nikon Z30 Lightroom profiles from pinned SpektraFilm stocks (experimental).")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("stocks", help="List goal stocks and why any are blocked")
    sub.add_parser("verify-source", help="Check the installed SpektraFilm commit")
    r = sub.add_parser("reference", help="Develop a Z30 NEF and render references")
    r.add_argument("--nef", type=Path, required=True)
    r.add_argument("--scene-id", required=True)
    r.add_argument("--stocks", nargs="+", default=["all"])
    r.add_argument("--work", type=Path, default=Path("results/z30"))
    k = sub.add_parser("probe-kit", help="Write probe LUTs for Camera Raw characterization")
    k.add_argument("--out", type=Path, required=True)
    c = sub.add_parser("characterize", help="Test where Camera Raw applies a profile LUT")
    c.add_argument("--nef", type=Path, required=True)
    c.add_argument("--scene-id", required=True)
    c.add_argument("--identity-export", type=Path, required=True)
    c.add_argument("--probe-export", type=Path, required=True)
    c.add_argument("--probe", required=True)
    c.add_argument("--work", type=Path, default=Path("results/z30"))
    f = sub.add_parser("fit", help="Fit one stock's LUT from training scenes")
    f.add_argument("--manifest", type=Path, required=True)
    f.add_argument("--stock", required=True)
    f.add_argument("--work", type=Path, default=Path("results/z30"))
    f.add_argument("--out", type=Path, default=Path("results/z30/luts"))
    e = sub.add_parser("evaluate", help="Look gate on held-out scenes")
    e.add_argument("--manifest", type=Path, required=True)
    e.add_argument("--stock", required=True)
    e.add_argument("--work", type=Path, default=Path("results/z30"))
    e.add_argument("--out", type=Path, default=Path("results/z30/look_gate"))
    s = sub.add_parser("status", help="Release gates for every goal stock")
    s.add_argument("--workspace", type=Path, default=Path("."))
    a = p.parse_args(argv)

    if a.cmd == "stocks":
        from .stocks import load_registry
        for key, v in load_registry().items():
            print(f"{key:14} {v['status']:18} {v['name']}" + ("" if v["status"] == "available" else f"  -- {v['notes']}"))
        return 0
    if a.cmd == "verify-source":
        from .reference import verify_spektrafilm_commit
        res = verify_spektrafilm_commit()
        print(json.dumps(res, indent=2))
        return 0 if res.get("verified") else 1
    if a.cmd == "reference":
        from .stocks import available_keys
        from .workflow import prepare_scene, reference_for
        scene = prepare_scene(a.nef, a.work, a.scene_id)
        for stock in (available_keys() if a.stocks == ["all"] else a.stocks):
            reference_for(scene, stock, a.work)
            print(f"{a.scene_id}: {stock} rendered")
        return 0
    if a.cmd == "probe-kit":
        from .probes import write_probe_kit
        print(json.dumps(write_probe_kit(a.out), indent=2))
        return 0
    if a.cmd == "characterize":
        import numpy as np
        from .evaluate import load_thresholds
        from .probes import characterize
        from .workflow import prepare_scene, registration_for, scene_blocks
        cfg = load_thresholds()
        scene = prepare_scene(a.nef, a.work, a.scene_id)
        reg = registration_for(scene, a.identity_export, a.work)
        lin = np.load(scene)
        ident = scene_blocks(scene, a.identity_export, reg, lin, cfg)
        probe = scene_blocks(scene, a.probe_export, reg, lin, cfg)
        keep = ident["keep"] & probe["keep"]
        res = characterize(ident["export_enc"][keep], probe["export_enc"][keep], a.probe)
        print(json.dumps(res, indent=2))
        return 0 if res["hypothesis_holds"] else 1
    if a.cmd == "fit":
        from .workflow import fit_stock
        print(json.dumps(fit_stock(a.manifest, a.stock, a.work, a.out), indent=2))
        return 0
    if a.cmd == "evaluate":
        from .workflow import evaluate_stock
        rep = evaluate_stock(a.manifest, a.stock, a.work, a.out)
        print(json.dumps(rep["pooled_heldout"], indent=2))
        return 0 if rep["pooled_heldout"]["pass"] else 1
    if a.cmd == "status":
        from .status import status
        res = status(a.workspace)
        print(json.dumps(res, indent=2))
        return 0 if res["goal_met"] else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
