import subprocess
import logging
from fastapi import UploadFile
import shutil
import tempfile
import json
from pathlib import Path
# from stt.config import settings
# from stt.common_exceptions import AudioProcessingError

from config import settings
from common_exceptions import AudioProcessingError
logger = logging.getLogger(__name__)

class AudioPreprocessor:
    def _get_audio_duration_ms(self, file_path: str) -> int:
        """
        Uses ffprobe to get the duration of an audio file in milliseconds.
        """
        command = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            file_path
        ]
        try:
            logger.info(f"Running ffprobe to get duration: {' '.join(command)}")
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)

            duration_s = None
            if 'format' in data and 'duration' in data['format']:
                duration_s = float(data['format']['duration'])
            else:
                for stream in data.get('streams', []):
                    if stream.get('codec_type') == 'audio' and 'duration' in stream:
                        duration_s = float(stream['duration'])
                        break
            
            if duration_s is None:
                logger.error(f"Could not determine audio duration for {file_path} from ffprobe output: {data}")
                raise AudioProcessingError(f"Could not determine audio duration for the file.")

            duration_ms = int(duration_s * 1000)
            logger.info(f"Determined audio duration for {file_path}: {duration_ms} ms")
            return duration_ms

        except subprocess.CalledProcessError as e:
            logger.error(f"ffprobe error while getting duration for {file_path}: {e.stderr}")
            raise AudioProcessingError(f"ffprobe failed to get audio duration: {e.stderr}")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding ffprobe JSON output for {file_path}: {e}")
            raise AudioProcessingError(f"Failed to parse ffprobe output for audio duration.")
        except Exception as e:
            logger.error(f"Unexpected error in _get_audio_duration_ms for {file_path}: {e}", exc_info=True)
            raise AudioProcessingError(f"An unexpected error occurred while determining audio duration: {str(e)}")


    def to_pcm(self, file: UploadFile) -> tuple[bytes, int]:
        """
        Converts an uploaded audio file to 16 kHz PCM WAV format bytes using ffmpeg.
        Also extracts audio duration using ffprobe.

        Returns:
            A tuple containing (pcm_audio_bytes, duration_ms).

        Raises:
            AudioProcessingError: If processing fails or audio duration exceeds the configured limit.
        """
        tmp_input_file_path = None
        tmp_output_file_path = None

        try:
            original_suffix = "".join(Path(file.filename).suffixes) if file.filename else ".tmp"
            with tempfile.NamedTemporaryFile(delete=False, suffix=original_suffix) as tmp_input_file:
                shutil.copyfileobj(file.file, tmp_input_file)
                tmp_input_file_path = tmp_input_file.name
            
            logger.info(f"Copied uploaded file to temporary path: {tmp_input_file_path}")

            duration_ms = self._get_audio_duration_ms(tmp_input_file_path)
            if duration_ms > (settings.max_audio_duration_seconds * 1000):
                msg = (
                    f"Audio duration ({duration_ms / 1000:.2f}s) exceeds maximum allowed "
                    f"({settings.max_audio_duration_seconds}s)."
                )
                logger.error(msg)
                raise AudioProcessingError(msg)

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_output_file:
                tmp_output_file_path = tmp_output_file.name

            command = [
                "ffmpeg",
                "-y",
                "-i", tmp_input_file_path,
                "-f", "wav",
                "-ar", "16000",
                "-ac", "1",
                "-hide_banner",
                "-loglevel", "error",
                tmp_output_file_path
            ]

            logger.info(f"Running ffmpeg for PCM conversion: {' '.join(command)}")
            process = subprocess.run(command, capture_output=True, check=False)

            ffmpeg_stderr_output = process.stderr.decode(errors='replace') if process.stderr else "No stderr output from ffmpeg."

            if process.returncode != 0:
                logger.error(f"ffmpeg failed with exit code {process.returncode} for {file.filename or 'uploaded file'}. ffmpeg stderr: {ffmpeg_stderr_output}")
                raise AudioProcessingError(f"Audio conversion by ffmpeg failed with exit code {process.returncode}. Details: {ffmpeg_stderr_output}")

            output_file = Path(tmp_output_file_path)
            if not output_file.exists() or output_file.stat().st_size == 0:
                logger.error(f"ffmpeg produced an empty output file for {file.filename or 'uploaded file'} (exit code 0). ffmpeg stderr: {ffmpeg_stderr_output}")
                raise AudioProcessingError(f"Audio conversion by ffmpeg resulted in an empty file (exit code 0). Relevant ffmpeg output: {ffmpeg_stderr_output}")

            with open(tmp_output_file_path, "rb") as f_pcm:
                pcm_bytes = f_pcm.read()

            logger.info(f"Successfully converted {file.filename or 'uploaded file'} to 16kHz WAV bytes. Size: {len(pcm_bytes)} bytes.")
            return pcm_bytes, duration_ms

        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.decode() if e.stderr else "ffmpeg failed with no stderr"
            logger.error(f"ffmpeg error during conversion of {file.filename or 'uploaded file'}: {err_msg}")
            raise AudioProcessingError(f"Audio conversion failed: {err_msg}")
        except AudioProcessingError:
            raise
        except Exception as e:
            logger.error(f"An unexpected error occurred during audio preprocessing of {file.filename or 'uploaded file'}: {e}", exc_info=True)
            raise AudioProcessingError(f"Audio preprocessing failed: {str(e)}")
        finally:
            if tmp_input_file_path and Path(tmp_input_file_path).exists():
                try:
                    Path(tmp_input_file_path).unlink()
                    logger.debug(f"Deleted temp input file: {tmp_input_file_path}")
                except Exception as e_rm:
                    logger.warning(f"Failed to delete temp input file {tmp_input_file_path}: {e_rm}")
            if tmp_output_file_path and Path(tmp_output_file_path).exists():
                try:
                    Path(tmp_output_file_path).unlink()
                    logger.debug(f"Deleted temp output file: {tmp_output_file_path}")
                except Exception as e_rm:
                    logger.warning(f"Failed to delete temp output file {tmp_output_file_path}: {e_rm}")