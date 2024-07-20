import json

import numpy as np
import torch
from pytube import YouTube
from transformers import pipeline
from transformers.utils import is_flash_attn_2_available

TRANSCRIBE_PIPELINE = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-large-v3",  # select checkpoint from https://huggingface.co/openai/whisper-large-v3#model-details
    torch_dtype=torch.float16,
    device="cuda:0",
    model_kwargs={"attn_implementation": "flash_attention_2"}
    if is_flash_attn_2_available()
    else {"attn_implementation": "sdpa"},
)


def transcribe(audio: tuple[int, np.ndarray]) -> str:
    sampling_rate, raw_audio = audio
    raw_audio = raw_audio.astype(np.float32)
    raw_audio /= np.max(np.abs(raw_audio))
    return TRANSCRIBE_PIPELINE({"sampling_rate": sampling_rate, "raw": raw_audio})["text"]


# TODO unify this with the `retrieval.file_mapping`
def get_youtube_video(url: str, base_path: str) -> dict:
    """Use a local OpenAI Whisper model to transcribe.

    Output schema:
        {
            "speakers": [],
            "chunks": [
                {
                    "timestamp": [
                        0.7,
                        3.5
                    ],
                     "text": ""
                }
                {
                    "timestamp": [
                        3.58,
                        9.16
                    ],
                     "text": ""
                }
            ],
            "text": "NOTE this top-level text includes the full transcriptions"
        }
    """

    yt = YouTube(url=url)
    # NOTE use itag(22). Others might be rate limited by YouTube or significantly slower
    # even for smaller files.
    stream = yt.streams.get_by_itag(22)

    output_path = stream.download(output_path=base_path)
    outputs = TRANSCRIBE_PIPELINE(
        output_path,
        chunk_length_s=30,
        batch_size=24,
        generate_kwargs=dict(task="transcribe", language=None),
        return_timestamps="chunk",
    )

    json.dump(outputs, open(f"{base_path}/{stream.default_filename}", "w"))

    return outputs


# TODO conver the returned JSONs of `get_youtube_video` to a table
# that matches ingestion.transcriptions and ingestion.transcriptions_table.
