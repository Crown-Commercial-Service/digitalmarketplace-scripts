#!/usr/bin/env python3
"""
Scan user uploaded PDFs in S3 and flag ones which contain any
non-text or image content (ie. JS or videos).

Requires a running version of veraPDF-REST (https://github.com/veraPDF/veraPDF-rest)
The simplest way is to use the Docker image provided by veraPDF. Run
docker run -p 8080:8080 verapdf/rest:latest
in a separate terminal window to pull the image and start it listening on http://localhost:8080

Set AWS_PROFILE to the relevant profile for the stage when running eg.
$ AWS_PROFILE=development-developer ./scripts/scan-pdf-content.py preview g-cloud-12 http://localhost:8080

By default this script will fetch a list of PDFs to scan from the relevant S3 bucket, but it can also
resume from a failed run. The PDF S3 keys are stored in a temporary file and if the index argument is
passed keys will be loaded from the file and the scan resumed from position `index`. The easiest way to
determine the correct index is to count the number of result rows in the report CSV.

Usage: scan-pdf-content.py <stage> <framework> <verapdf-url> [--index=<index>]

Options:
    <stage>                         Stage to target
    <framework>                     Slug for the framework to scan
    <verapdf-url>                   The url for the verapdf-rest service to use
    --index=<index>                 Optional. If supplied, the scan resumes from a previous run, using
                                        the list of PDFs stored in '/tmp/pdf-scan-queue.json' starting at `index`

    -h, --help                      Show this information

Examples:
    ./scripts/scan-pdf-content.py staging g-cloud-12 http://localhost:8080
    ./scripts/scan-pdf-content.pt preview g-cloud-12 http://localhost:8080 --index 50
"""
import csv
import json
import logging
import os
import threading
import queue
from datetime import datetime
from typing import Tuple, NamedTuple, Optional
import boto3
import requests
from docopt import docopt


class ScanResult(NamedTuple):
    scanned_at: str
    status_code: int
    message: str
    bucket: str
    framework: str
    key: str


def list_pdfs_in_bucket(bucket_name: str, framework: str,) -> list:
    """
    Return a list of `ObjectSummary`s for PDFs in the supplied S3 bucket.

    :param bucket_name: The name of the bucket to check
    :param framework: The name of the framework to scan for
    :return: A list of S3 objects
    """
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(bucket_name)
    all_objects = bucket.objects.filter(Prefix=f"{framework}/documents")

    # Filter to just PDFs & convert boto's object collection into a list
    return [i for i in all_objects if i.key.endswith(".pdf")]


def save_all_pdf_names_to_scan(pdfs: list) -> None:
    """
    Save a list of `ObjectSummary`s representing PDFs stored on S3 to a temporary file.

    :param pdfs: The list of objects to save
    :returns: None
    """
    logging.info("Writing PDFs to scan to /tmp/pdf-scan-queue.json")
    with open("/tmp/pdf-scan-queue.json", "w") as f:
        for pdf in pdfs:
            f.write(json.dumps({"bucket_name": pdf.bucket_name, "key": pdf.key}))
            f.write("\n")


def load_pdfs_to_scan_from_file() -> list:
    """
    Load a list of PDFs to scan from a temporary file and convert to `ObjectSummary`s.

    :return: A list of `ObjectSummary`s
    """
    s3 = boto3.resource("s3")
    with open("/tmp/pdf-scan-queue.json", "r") as f:
        logging.info("Loading files to scan from /tmp/pdf-scan-queue.json")
        lines = [json.loads(line) for line in f.readlines()]

    return [s3.ObjectSummary(line["bucket_name"], line["key"]) for line in lines]


def fetch_s3_object_to_memory(object_summary,) -> bytes:
    """
    Download the contents of an object in S3 into an in-memory variable.

    :param object_summary: An `ObjectSummary` for an object stored in S3
    :return: The contents of the supplied object
    """
    s3 = boto3.resource("s3")
    return (
        s3.Object(object_summary.bucket_name, object_summary.key).get()["Body"].read()
    )


def contains_unusual_content(result: dict) -> bool:
    """
    returns True if the response indicates the PDF contains unusual content
    (Launch, Sound, Movie, ResetForm, ImportData and JavaScript actions)
    by checking if ISO 19005.1 clause 6.6.1 is among the failure reasons.

    :param result: The parsed JSON response from POSTing a PDF to verapdf
    :return: True if the PDF contains unusual content, otherwise False
    """
    assertions = result["testAssertions"]

    for assertion in assertions:
        status = assertion["status"]
        specification = assertion["ruleId"]["specification"]
        clause = assertion["ruleId"]["clause"]
        if status == "FAILED" and specification == "ISO_19005_1" and clause == "6.6.1":
            return True

    return False


def scan_object(verapdf_url: str, file_to_scan: bytes) -> Tuple[int, str]:
    """
    Scan an in-memory file against verapdf to see if it contains
    non-text or image content.

    :param file_to_scan: The in-memory file contents to scan
    :param verapdf_url: The base url to a verapdf-rest service
    :return: (`status_code`, `message`) where `status_code` is
        the HTTP status code from verapdf and `message` is one
        of "No unusual content types", "Unusual content types
        detected", and "Error"
    """
    response = requests.post(
        # Scan against profile '1B' because that contains the ISO
        # specification we need to detect content types
        verapdf_url + "/api/validate/1b",
        files={"file": file_to_scan},
        headers={"Accept": "application/json"},
    )

    if response.status_code != 200:
        return response.status_code, "Error"

    if contains_unusual_content(response.json()):
        return response.status_code, "Unusual content types detected"
    else:
        return response.status_code, "No unusual content types"


def set_up_report_file(filename: str) -> None:
    """
    Create an empty CSV with headers to store results

    :param filename: The name of the output file to create
    :returns: None
    """
    with open(filename, "w") as f:
        report_writer = csv.writer(f, delimiter=",")
        report_writer.writerow(
            ["scanned_at", "bucket", "framework", "key", "status_code", "message"]
        )


def write_result(filename: str, scan: ScanResult) -> None:
    """
    Write the result of a scan to the report CSV

    :param filename: The name of the output file to write to
    :param scan: A `ScanResult`
    :returns: None
    """
    with open(filename, "a") as f:
        report_writer = csv.writer(f, delimiter=",")
        report_writer.writerow(
            [
                scan.scanned_at,
                scan.bucket,
                scan.framework,
                scan.key,
                scan.status_code,
                scan.message,
            ]
        )


def scan_pdf(scan_queue: queue.Queue, verapdf_url: str, report_name: str):
    """
    Worker function. Get a PDF from the queue, download, scan and write the results to `report_name`.

    :param scan_queue: The queue to get tasks from
    :param verapdf_url: The base URL to a verapdf-rest service
    :param report_name: The file to write scan results to
    :return: None
    """
    while not scan_queue.empty():
        i, pdf_summary = scan_queue.get()

        if i % 10 == 0:
            logging.info(f"Scanning file {i}")

        pdf_content = fetch_s3_object_to_memory(pdf_summary)
        code, message = scan_object(verapdf_url, pdf_content)
        scan_result = ScanResult(
            scanned_at=str(datetime.now()),
            status_code=code,
            message=message,
            bucket=pdf_summary.bucket_name,
            framework=framework,
            key=pdf_summary.key,
        )

        write_result(report_name, scan_result)
        scan_queue.task_done()


def scan_all_pdfs(
    bucket_name: str,
    verapdf_url: str,
    framework: str,
    report_name: str,
    index: Optional[int] = None
) -> None:
    """
    Scan all pdfs in an S3 bucket against verapdf to see if any
    contain JS, videos or any other unusual content types.

    :param bucket_name: The S3 bucket to scan
    :param verapdf_url: The base url to a verapdf-rest service
    :param framework: The framework slug to scan, eg. g-cloud-12
    :param report_name: The file to write scan results to
    :param index: An optional index to resume from. If supplied, a list of PDFs to scan is read from
                    '/tmp/pdf-scan-queue.json' and the scan is started from position `index`.
    :return: None
    """
    if index is not None:
        # Resuming from a previous run. Load files to scan from disk and set up index
        logging.info("Resuming from previous run")
        pdfs_to_scan = load_pdfs_to_scan_from_file()

        logging.info(f"Resuming scan from position: {index}")
        pdfs_to_scan = pdfs_to_scan[index:]

    else:
        # Starting new scan. Get files to scan from S3
        pdfs_to_scan = list_pdfs_in_bucket(bucket_name, framework)

    total_to_scan = len(pdfs_to_scan)

    save_all_pdf_names_to_scan(pdfs_to_scan)
    logging.info(f"Scanning {total_to_scan} files")

    # Put all tasks into a queue
    scan_queue = queue.Queue()
    for i, pdf in enumerate(pdfs_to_scan):
        scan_queue.put((i, pdf))

    # Start threads
    for _ in range(3):
        threading.Thread(
            target=scan_pdf,
            args=(scan_queue, verapdf_url, report_name)
        ).start()

    # Wait for threads to finish
    scan_queue.join()

    logging.info("Finished scanning")
    logging.info("Removing temporary file /tmp/pdf-scan-queue.json")
    os.remove("/tmp/pdf-scan-queue.json")


if __name__ == "__main__":
    args = docopt(__doc__)

    stage = args["<stage>"]
    framework = args["<framework>"]
    verapdf_url = args["<verapdf-url>"]
    index = None

    if args.get("--index"):
        if not os.path.exists("/tmp/pdf-scan-queue.json"):
            raise FileNotFoundError("--index was supplied but no file found at /tmp/pdf-scan-queue.json")
        index = int(args["--index"])

    logging.basicConfig(level=logging.INFO)

    s3_bucket = f"digitalmarketplace-documents-{stage}-{stage}"

    report_name = f"pdf_scan_results_{stage}-{framework}.csv"
    if index is None:
        # Only set up a new report file if this is a new run
        set_up_report_file(report_name)

    scan_all_pdfs(s3_bucket, verapdf_url, framework, report_name, index)
    logging.info(f"Wrote report to ./{report_name}")
