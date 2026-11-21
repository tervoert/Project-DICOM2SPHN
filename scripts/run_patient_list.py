#!/usr/bin/env python
"""Run Project-DICOM2SPHN for every DICOM PatientID listed in a text file.

The input file contains one DICOM PatientID per line. Empty lines and lines
starting with '#' are ignored, and duplicate PatientIDs are processed only once.

Every patient is processed in a separate 'python -m dicom2sphn' subprocess, so each
run starts with a fresh logger, DataStore and DICOMweb session. With --jobs N, up to
N patients are processed in parallel.

Output of each dicom2sphn run:
    - sequential (--jobs 1) without --log_dir: streamed directly to the console
    - parallel   (--jobs >1) without --log_dir: captured, and printed as one block per patient when it finishes
    - with --log_dir: written to '<log_dir>/<PatientID>.log' (one file per patient)

Exit codes of dicom2sphn (per patient):
    0  success, JSON exported
    1  error (invalid input parameters or configuration)
    2  nothing exported (no subject pseudo identifier and/or no imaging procedures)

Exit code of this script:
    0  every patient returned 0 or 2
    1  at least one patient returned 1 (or another unexpected exit code)

Examples:
    python scripts/run_patient_list.py patient_ids.txt -c config.toml
    python scripts/run_patient_list.py patient_ids.txt -c config.toml --jobs 4 --log_dir output/logs
    python scripts/run_patient_list.py patient_ids.txt -c config.toml --output_dir D:/sphn_export

    Creating the patient list from Orthanc DICOM server:
    curl -s -u orthanc:orthanc "http://localhost:8042/dicom-web/studies?includefield=00100020" | jq -r '[.[]."00100020".Value[]?] | unique | .[]' > patient_ids.txt
"""

import argparse
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from datetime import timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"

EXIT_CODE_MEANING = {
    0: "exported",
    1: "error",
    2: "nothing exported",
}

print_lock = threading.Lock()  # Keeps the output of parallel runs from interleaving


def log(message: str) -> None:
    """Print a message from this script (thread-safe)."""
    with print_lock:
        print(message)


def read_patient_ids(patient_id_file: Path) -> list[str]:
    """Read PatientIDs (one per line), skipping empty lines, '#' comments and duplicates."""
    patient_ids: list[str] = []
    seen: set[str] = set()
    with patient_id_file.open(encoding="utf-8-sig") as f:  # utf-8-sig: tolerate a BOM (e.g. files saved by Excel/Notepad)
        for line in f:
            patient_id = line.strip()
            if not patient_id or patient_id.startswith("#"):
                continue
            if patient_id in seen:
                print(f"Warning: duplicate PatientID '{patient_id}' is skipped.")
                continue
            seen.add(patient_id)
            patient_ids.append(patient_id)
    return patient_ids


def log_file_name(patient_id: str) -> str:
    """Return a safe log file name for a PatientID (characters not allowed in file names are replaced by '_')."""
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", patient_id).strip(" .") + ".log"


def run_dicom2sphn(patient_id: str, output_spec: str, config_file: str, capture: bool, log_dir: Path | None) -> tuple[int, str]:
    """Run dicom2sphn for one PatientID in a subprocess.

    Returns the exit code and the captured output (empty if the output was streamed to the console or a log file).
    """
    env = os.environ.copy()
    # Make 'python -m dicom2sphn' work even if the package is not installed with 'pip install -e .'
    env["PYTHONPATH"] = str(SRC_DIR) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    command = [
        sys.executable, "-m", "dicom2sphn",
        "--patient_id", patient_id,
        "--output_file_path_specification", output_spec,
        "--config_file", config_file,
    ]

    if log_dir is not None:
        with (log_dir / log_file_name(patient_id)).open("w", encoding="utf-8") as log_file:
            return subprocess.run(command, env=env, check=False, stdout=log_file, stderr=subprocess.STDOUT).returncode, ""

    if capture:
        result = subprocess.run(command, env=env, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace")
        return result.returncode, result.stdout

    return subprocess.run(command, env=env, check=False).returncode, ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Project-DICOM2SPHN for every DICOM PatientID in a file (one PatientID per line).")
    parser.add_argument("patient_id_file", type=Path, help="Text file with one DICOM PatientID per line")
    parser.add_argument("-c", "--config_file", default="config.toml", help="Configuration file (default: config.toml)")
    parser.add_argument("-o", "--output_file_path_specification", default="output/output_patient_{patient_id}_{file_id}.json",
                        help="Output file path specification, must contain '{patient_id}' and '{file_id}' "
                             "(default: output/output_patient_{patient_id}_{file_id}.json)")
    parser.add_argument("-d", "--output_dir", type=Path, default=None,
                        help="Folder for the output JSON files. Replaces the folder part of --output_file_path_specification "
                             "(the file name pattern is kept). The folder is created if it does not exist.")
    parser.add_argument("-j", "--jobs", type=int, default=1,
                        help="Number of patients processed in parallel (default: 1). "
                             "Each job opens its own DICOMweb session, so keep this modest to avoid overloading the server.")
    parser.add_argument("--log_dir", type=Path, default=None,
                        help="Write the output of each patient to '<log_dir>/<PatientID>.log' instead of the console")
    parser.add_argument("--stop_on_error", action="store_true",
                        help="Stop at the first patient that returns an error (exit code 1). "
                             "With --jobs > 1, patients that are already running are finished, but no new ones are started.")
    args = parser.parse_args()

    # Flush every line, so this script's output stays in order with the dicom2sphn subprocess output (also when redirected to a file)
    sys.stdout.reconfigure(line_buffering=True)

    if args.jobs < 1:
        print("Error: --jobs must be 1 or higher.")
        return 1

    if not args.patient_id_file.is_file():
        print(f"Error: PatientID file '{args.patient_id_file}' does not exist or is not a file.")
        return 1

    patient_ids = read_patient_ids(args.patient_id_file)
    if not patient_ids:
        print(f"Error: no PatientIDs found in '{args.patient_id_file}'.")
        return 1

    if args.log_dir is not None:
        args.log_dir.mkdir(parents=True, exist_ok=True)

    # Output folder: --output_dir replaces the folder part of the specification, the file name pattern is kept
    output_spec = Path(args.output_file_path_specification)
    if args.output_dir is not None:
        output_spec = args.output_dir / output_spec.name
    args.output_file_path_specification = str(output_spec)
    # dicom2sphn does not create the output folder itself (skipped if the folder part contains placeholders)
    if "{" not in str(output_spec.parent):
        output_spec.parent.mkdir(parents=True, exist_ok=True)

    n = len(patient_ids)
    jobs = min(args.jobs, n)
    capture = jobs > 1 and args.log_dir is None
    print(f"Processing {n} patient(s) from '{args.patient_id_file}' with {jobs} parallel job(s).")
    print(f"Writing the output JSON files to '{output_spec.parent}'.")
    if args.log_dir is not None:
        print(f"Writing the output of each patient to '{args.log_dir}'.")

    results: dict[str, tuple[int, float]] = {}
    start_all = time.perf_counter()

    def process(i: int, patient_id: str) -> int:
        log(f"[{i}/{n}] PatientID '{patient_id}': started")
        start = time.perf_counter()
        exit_code, output = run_dicom2sphn(patient_id, args.output_file_path_specification, args.config_file, capture, args.log_dir)
        duration = time.perf_counter() - start
        results[patient_id] = (exit_code, duration)
        with print_lock:
            if output:
                print(f"----- output of PatientID '{patient_id}' " + "-" * 40)
                print(output.rstrip())
                print("-" * 80)
            print(f"[{i}/{n}] PatientID '{patient_id}': exit code {exit_code} "
                  f"({EXIT_CODE_MEANING.get(exit_code, 'unexpected')}) in {timedelta(seconds=round(duration))}")
        return exit_code

    stopped = False
    with ThreadPoolExecutor(max_workers=jobs) as executor:
        todo = list(enumerate(patient_ids, start=1))
        running: set[Future] = set()
        while todo or running:
            # Keep at most 'jobs' patients running; only start new ones if we are not stopping
            while todo and len(running) < jobs and not stopped:
                i, patient_id = todo.pop(0)
                running.add(executor.submit(process, i, patient_id))
            if not running:
                break
            done, running = wait(running, return_when=FIRST_COMPLETED)
            if args.stop_on_error and not stopped and any(f.result() not in (0, 2) for f in done):
                stopped = True
                log("Stopping because of --stop_on_error (waiting for running patients to finish).")

    # Summary
    print("\n" + "=" * 80)
    print(f"Summary ({len(results)} of {n} patient(s) processed "
          f"in {timedelta(seconds=round(time.perf_counter() - start_all))}):")
    for code, meaning in EXIT_CODE_MEANING.items():
        print(f"  {meaning:<17}: {sum(1 for c, _ in results.values() if c == code)}")
    failed = [(pid, results[pid][0]) for pid in patient_ids if pid in results and results[pid][0] not in (0, 2)]
    if failed:
        print("  Failed PatientIDs:")
        for pid, c in failed:
            print(f"    {pid} (exit code {c})")
    not_processed = [pid for pid in patient_ids if pid not in results]
    if not_processed:
        print(f"  Not processed (stopped early): {len(not_processed)}")
    print("=" * 80)

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
