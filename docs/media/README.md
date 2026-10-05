# Published validation demo

The selected annotated pilot3B clip is intentionally included for the portfolio. Raw videos, observations, and model weights remain excluded. The approximately 18-second H.264 MP4 has no audio. Its overlay shows raw angles and cumulative saved replay decisions, displayed only after their recorded decision times. It is not a live classifier. Playback uses nominal FPS; overlay timestamps are source timestamps.

Regenerate with `python examples/render_validation_demo.py` using the private files and OpenCV. Encode the intermediate video using FFmpeg with `-c:v libx264 -crf 24 -pix_fmt yuv420p -movflags +faststart -an`. An optional encoder is available through `python -m pip install imageio-ffmpeg`; locate it with `imageio_ffmpeg.get_ffmpeg_exe()`. The core verifier does not require that helper.
