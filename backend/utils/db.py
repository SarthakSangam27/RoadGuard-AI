import sqlite3
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(
    __file__
).resolve().parent.parent

DATABASE_PATH = (
    BASE_DIR / "roadguard.db"
)


def get_connection():
    """
    Create a SQLite database connection.
    """

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = (
        sqlite3.Row
    )

    return connection


def initialize_database():
    """
    Create the scans table if it
    does not already exist.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            filename TEXT NOT NULL,

            pothole_detected INTEGER NOT NULL,

            vgg19_label TEXT,

            vgg19_confidence REAL,

            yolo_num_detections INTEGER DEFAULT 0,

            yolo_detections_json TEXT,

            processing_time_sec REAL,

            created_at TEXT NOT NULL
        )
        """
    )

    connection.commit()

    connection.close()


def save_scan(
    filename,
    pothole_detected,
    vgg19_label=None,
    vgg19_confidence=None,
    yolo_num_detections=0,
    yolo_detections_json=None,
    processing_time_sec=None,
):
    """
    Save a completed RoadGuard-AI scan.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO scans (
            filename,
            pothole_detected,
            vgg19_label,
            vgg19_confidence,
            yolo_num_detections,
            yolo_detections_json,
            processing_time_sec,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            filename,
            int(pothole_detected),
            vgg19_label,
            vgg19_confidence,
            yolo_num_detections,
            yolo_detections_json,
            processing_time_sec,
            datetime.utcnow().isoformat(),
        ),
    )

    scan_id = cursor.lastrowid

    connection.commit()

    connection.close()

    return scan_id


def get_all_scans():
    """
    Return all saved scans.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM scans
        ORDER BY created_at DESC
        """
    )

    rows = cursor.fetchall()

    connection.close()

    return [
        dict(row)
        for row in rows
    ]


def get_scan(scan_id):
    """
    Return one scan by ID.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM scans
        WHERE id = ?
        """,
        (scan_id,),
    )

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)


def delete_scan(scan_id):
    """
    Delete one scan.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM scans
        WHERE id = ?
        """,
        (scan_id,),
    )

    deleted = (
        cursor.rowcount > 0
    )

    connection.commit()

    connection.close()

    return deleted