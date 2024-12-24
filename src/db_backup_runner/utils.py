"""Utility functions"""

import bz2
import gzip
import lzma
from pathlib import Path
from typing import IO

from db_backup_runner.types import CompressionAlgorithm

compression_algorithms: list[CompressionAlgorithm] = [
    "gzip",
    "lzma",
    "xz",
    "bz2",
    "plain",
]

DEFAULT_BACKUP_DIR = Path("/tmp/db_backup_runner")


def get_compressed_file_extension(algorithm: CompressionAlgorithm) -> str:
    if algorithm == "gzip":
        return ".gz"
    elif algorithm in ["lzma", "xz"]:
        return ".xz"
    elif algorithm == "bz2":
        return ".bz2"
    elif algorithm == "plain":
        return ".raw"
    raise ValueError(f"Unknown compression method {algorithm}")


def open_file_compressed(file_path: Path, algorithm: CompressionAlgorithm) -> IO[bytes]:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.touch(mode=0o600)

    if algorithm == "gzip":
        return gzip.open(file_path, mode="wb")  # type:ignore
    elif algorithm in ["lzma", "xz"]:
        return lzma.open(file_path, mode="wb")
    elif algorithm == "bz2":
        return bz2.open(file_path, mode="wb")
    elif algorithm == "plain":
        return file_path.open(mode="wb")
    raise ValueError(f"Unknown compression method {algorithm}")
