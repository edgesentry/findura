import argparse
import json
import uuid

from harness.db import get_connection, init_db
from harness.ingest import ingest_file
from harness.loader import load_records
from harness.models import RunManifest
from harness.normalize import load_mapping, normalize_batch
from harness.pack import build_evidence_pack, compute_result_sha256
from harness.query import run_insurer_query


def main():
    parser = argparse.ArgumentParser(
        prog="harness",
        description="Inspectra deterministic inspection agent harness CLI",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # harness ingest
    ingest_p = subparsers.add_parser("ingest", help="Ingest raw inspection file")
    ingest_p.add_argument("file", help="Path to input file (CSV)")

    # harness review
    subparsers.add_parser("review", help="Review gate queue (Phase 2 stub)")

    # harness normalize
    norm_p = subparsers.add_parser(
        "normalize", help="Normalize raw batch using approved mapping and load into DB"
    )
    norm_p.add_argument(
        "--file", default=None, help="Path to CSV file (if not specified, use synthetic fixture)"
    )
    norm_p.add_argument(
        "--mapping",
        default="mappings/sources/source_csv_synthetic.yaml",
        help="Path to mapping YAML",
    )

    # harness query
    query_p = subparsers.add_parser("query", help="Run deterministic profile query")
    query_p.add_argument(
        "--profile", required=True, choices=["insurer"], help="Profile name"
    )
    query_p.add_argument(
        "--as-of", required=True, help="Reference date (YYYY-MM-DD)"
    )

    # harness pack
    pack_p = subparsers.add_parser("pack", help="Build evidence pack and run manifest")
    pack_p.add_argument(
        "--profile", required=True, choices=["insurer"], help="Profile name"
    )
    pack_p.add_argument(
        "--as-of", required=True, help="Reference date (YYYY-MM-DD)"
    )
    pack_p.add_argument(
        "--output", default=None, help="Path to output evidence pack JSON"
    )

    args = parser.parse_args()

    conn = get_connection()
    init_db(conn)

    if args.command == "ingest":
        batch = ingest_file(args.file, conn)
        print(f"Ingested: {batch.raw_locator}")
        print(f"input_sha256: {batch.input_sha256}")
        print(f"Rows: {len(batch.rows)}")

    elif args.command == "review":
        print("ReviewGate: 0 pending candidates in queue (Phase 1 mode).")

    elif args.command == "normalize":
        file_path = args.file or "fixtures/synthetic/synthetic_inspections.csv"
        batch = ingest_file(file_path, conn)
        mapping = load_mapping(args.mapping)
        records = normalize_batch(batch, mapping)
        verdicts = load_records(
            records,
            conn,
            input_sha256=batch.input_sha256,
            ontology_version="1",
            mapping_version=str(mapping.get("version", "1")),
        )
        accepted = sum(1 for v in verdicts if v.accepted)
        quarantined = sum(1 for v in verdicts if not v.accepted)
        print("Normalization & Graph Loading complete:")
        print(f"  Accepted: {accepted}")
        print(f"  Quarantined: {quarantined}")

    elif args.command == "query":
        result = run_insurer_query(conn, as_of=args.as_of)
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.command == "pack":
        # Run query and build evidence pack
        file_path = "fixtures/synthetic/synthetic_inspections.csv"
        batch = ingest_file(file_path, conn)
        mapping = load_mapping("mappings/sources/source_csv_synthetic.yaml")
        result = run_insurer_query(conn, as_of=args.as_of)

        run_id = str(uuid.uuid4())
        manifest = RunManifest(
            run_id=run_id,
            ontology_version="1",
            mapping_version=str(mapping.get("version", "1")),
            query_version="insurer-open-findings-v1",
            input_sha256=batch.input_sha256,
            as_of=args.as_of,
        )

        pack = build_evidence_pack(manifest, profile=args.profile, result=result)
        result_hash = compute_result_sha256(
            as_of=args.as_of,
            input_sha256=batch.input_sha256,
            mapping_version=manifest.mapping_version,
            ontology_version=manifest.ontology_version,
            profile=args.profile,
            query_version=manifest.query_version,
            result=result,
        )

        out_json = json.dumps(pack, indent=2, ensure_ascii=False)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(out_json)
            print(f"Evidence pack written to: {args.output}")
        else:
            print(out_json)
        print(f"result_sha256: {result_hash}")


if __name__ == "__main__":
    main()
