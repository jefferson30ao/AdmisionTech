import os
import json
from datetime import datetime, timezone

class Logger:
    def __init__(self, base_log_dir="logs"):
        self.base_log_dir = base_log_dir

    def _ensure_log_directory(self, log_date_dir):
        """Asegura que el directorio de logs para la fecha actual exista."""
        os.makedirs(log_date_dir, exist_ok=True)

    def _get_log_filepath(self, log_date_dir, module):
        """Determina la ruta completa del archivo de log."""
        current_time_str = datetime.now(timezone.utc).strftime("%H-%M-%S")
        filename = f"{module}_{current_time_str}.jsonl"
        return os.path.join(log_date_dir, filename)

    def log(self, level: str, module: str, message: str, extra: dict = None):
        """
        Registra un mensaje de log en un archivo JSONL.

        Args:
            level (str): Nivel del log (INFO, ERROR, BENCH).
            module (str): Módulo de origen (validation, execution, benchmark, general, etc.).
            message (str): Mensaje descriptivo del evento.
            extra (dict, optional): Diccionario opcional con datos de contexto adicionales.
        """
        if extra is None:
            extra = {}

        now_utc = datetime.now(timezone.utc)
        timestamp_iso = now_utc.isoformat(timespec='milliseconds').replace('+00:00', 'Z')

        log_entry = {
            "timestamp": timestamp_iso,
            "level": level,
            "module": module,
            "message": message,
            "extra": extra
        }

        today_str = now_utc.strftime("%Y-%m-%d")
        log_date_dir = os.path.join(self.base_log_dir, today_str)

        self._ensure_log_directory(log_date_dir)
        log_filepath = self._get_log_filepath(log_date_dir, module)

        with open(log_filepath, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
