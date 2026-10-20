"""Conservative Phase 1 release gate: never turn tests into a fidelity claim."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
from typing import Any
from .stocks import supported_stock


def phase1_status(workspace: Path) -> dict[str, Any]:
    """Inspect concrete evidence from an experiment workspace.

    Release readiness requires independent device evidence. This audit does
    not automatically accept claimed hardware success: the operator must
    inspect original photos and physical camera import outcomes. The reported
    status remains gated until those are supplied.
    """
    workspace=Path(workspace)
    stock=supported_stock('portra160')
    reference_file=workspace/'results'/'portra160_reference.npy'
    reference_meta=reference_file.with_suffix('.json')
    kit_file=workspace/'build'/'portra160_camera_probes'/'manifest.json'
    fuji_backup=workspace/'results'/'hardware'/'x100v_backup_manifest.json'
    fuji_diagnostic=workspace/'results'/'hardware'/'x100v_c5'/'DSCF4330_comparison_report.json'
    fuji_held_out=workspace/'results'/'hardware'/'x100v_c6'/'DSCF4360_comparison_report.json'
    fuji_provisional=workspace/'results'/'hardware'/'x100v_c6'/'x100v_c6_provisional_candidate_report.json'
    camera_files={
      'nikon_zf': workspace/'results'/'zf_portra160_measured_candidate.json',
      'fujifilm_x100v': workspace/'results'/'x100v_portra160_measured_candidate.json',
    }
    gates={
       'exact_upstream_stock': True,
       'spektrafilm_available_in_runtime': importlib.util.find_spec('spektrafilm') is not None,
       'reference_image_exists': reference_file.is_file(),
       'reference_metadata_exists': reference_meta.is_file(),
       'camera_probe_manifest_exists': kit_file.is_file(),
       'fujifilm_read_only_backup_manifest_exists': fuji_backup.is_file(),
       'fujifilm_single_scene_diagnostic_exists': fuji_diagnostic.is_file(),
       'fujifilm_held_out_diagnostic_exists': fuji_held_out.is_file(),
       'fujifilm_provisional_candidate_report_exists': fuji_provisional.is_file(),
       'nikon_measured_candidate_report_exists': camera_files['nikon_zf'].is_file(),
       'fujifilm_measured_candidate_report_exists': camera_files['fujifilm_x100v'].is_file(),
       'nikon_actual_camera_acceptance_confirmed': False,
       'fujifilm_actual_camera_application_confirmed': False,
       'held_out_color_validation_completed': False,
    }
    if reference_meta.is_file():
        try:
            m=json.loads(reference_meta.read_text(encoding='utf-8'))
            gates['reference_metadata_consistent']=(
                m.get('film')==stock['film'] and m.get('print')==stock['print']
                and m.get('mode')=='color')
        except (json.JSONDecodeError, OSError):
            gates['reference_metadata_consistent']=False
    else:
        gates['reference_metadata_consistent']=False
    # File existence only proves an artifact was saved. Hardware verification
    # and withheld-scene measurement cannot be inferred from that.
    ready=all(gates.values())
    return {
      'phase':'portra160_measured_camera_emulation',
      'ready_for_everyday_use':ready,
      'status':'ready' if ready else 'NOT READY: measurable output and hardware tests required',
      'gates':gates,
      'source_stock':stock['film'],
      'source_print':stock['print'],
      'note':'Phase1 readout intentionally never grants hardware verification based solely on files. An X100V read-only backup and held-out diagnostic are recorded, but no custom-setting write, property-level readback, measured chart calibration, image-quality acceptance, or Nikon hardware test has been completed.',
    }
