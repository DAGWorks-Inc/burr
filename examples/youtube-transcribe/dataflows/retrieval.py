import pickle
import subprocess
from pathlib import Path

import lancedb
import pyarrow as pa


def file_mapping(
    base_dir: str,
    mapping_file_path: str = "./file_mapping.pkl",
) -> dict:
    """Create a mapping from {file_name: absolute map} to create a catalog
    of all available videos. This can be expensive, so we pickle it to
    reuse it on subsequent runs.
    """
    if Path(mapping_file_path).exists():
        mapping = pickle.loads(Path(mapping_file_path).read_bytes())
    else:
        base_dir = Path(base_dir)
        subdirectories = [p for p in base_dir.rglob("*") if p.is_dir()]

        mapping = dict()

        for dir in subdirectories:
            for p in dir.iterdir():
                if p.is_file() and p.suffix.lower() == ".mp4":
                    mapping[p.name] = p

        pickle.dump(mapping, mapping_file_path.open("wb"))

    return mapping


def search_results(
    transcriptions_table: lancedb.table.Table,
    search_input: str,
    top_k: int = 3,
) -> pa.Table:
    """LanceDB query to"""
    search_query = (
        transcriptions_table.search(search_input)
        .select(["text", "file_name", "start"])
        .limit(top_k)
    )
    return search_query.to_arrow()


def selected_result(search_results: pa.Table) -> dict:
    return search_results.to_pandas().to_dict(orient="records")[0]


def open_resource(
    selected_result: dict,
    file_mapping: dict,
    vlc_windows_path: str = "/mnt/c/Program Files (x86)/VideoLAN/VLC/vlc.exe",
) -> None:
    """Launch VLC to open the selected video at the timestamp of the transcription"""
    video_path = file_mapping[selected_result["file_name"]]
    # Line to convert a Windows path to valid WSL2 path, using the mounted D:/ drive via /mnt/d/
    videos_windows_path = str(video_path).replace("/mnt/d/", "D:\\").replace("/", "\\")

    timestamp = selected_result["start"] - 1
    subprocess.Popen(
        [
            vlc_windows_path,
            "--start-time",
            str(timestamp),
            videos_windows_path,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
