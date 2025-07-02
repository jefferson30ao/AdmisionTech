from fastapi import FastAPI, UploadFile, File, Form
from starlette.responses import FileResponse, StreamingResponse
import pandas as pd
import io
import json
import os
from datetime import datetime
from frontend.utils.logger import Logger
from frontend.config_utils import load_scoring_config
from frontend.evaluation_logic import run_serial, run_openmp, run_cuda, run_pthreads
from frontend.benchmark_logic import run_full_benchmark

logger = Logger()

def setup_api_routes(app: FastAPI):
    @app.post("/upload")
    async def upload_files(students_file: UploadFile = File(...), key_file: UploadFile = File(...)):
        try:
            students_content = await students_file.read()
            key_content = await key_file.read()

            app.state.students_df = pd.read_excel(io.BytesIO(students_content))
            # Renombrar la columna 'DNI' a 'student_id' para que coincida con la lógica de evaluación
            if 'DNI' in app.state.students_df.columns:
                app.state.students_df.rename(columns={'DNI': 'student_id'}, inplace=True)
            app.state.key_df = pd.read_excel(io.BytesIO(key_content))
            logger.log("INFO", "file_upload", "Archivos cargados exitosamente.", extra={"students_file": students_file.filename, "key_file": key_file.filename})
            return {"status": "ok"}
        except Exception as e:
            logger.log("ERROR", "file_upload", f"Error al cargar archivos: {str(e)}", extra={"error_details": str(e)})
            return {"status": "error", "message": str(e)}

    @app.post("/run")
    async def run_evaluation(
        mode: str = Form(...),
    ):
        try:
            if not hasattr(app.state, 'students_df') or not hasattr(app.state, 'key_df'):
                logger.log("ERROR", "validation", "Archivos de estudiantes o clave no cargados.", extra={"rule_id": "RF-02"})
                return {"status": "error", "message": "Archivos de estudiantes o clave no cargados."}

            students_df = app.state.students_df
            key_df = app.state.key_df
            # Leer configuración de puntuación desde el archivo en cada ejecución
            scoring_config_current = load_scoring_config()
            chunk_size = scoring_config_current.get('chunk_size', 0)
            scoring_rules = scoring_config_current.get('scoring', {"correct": 0.0, "wrong": 0.0, "blank": 0.0})

            if chunk_size > 0:
                all_results_list = []
                num_students = len(students_df)
                for i in range(0, num_students, chunk_size):
                    chunk_df = students_df.iloc[i:i + chunk_size]
                    if mode == "serial":
                        chunk_results_df = run_serial(chunk_df, key_df['correct_answer'], scoring_rules)
                    elif mode == "openmp":
                        chunk_results_df = run_openmp(chunk_df, key_df['correct_answer'], scoring_rules)
                    elif mode == "cuda":
                        chunk_results_df = run_cuda(chunk_df, key_df['correct_answer'], scoring_rules)
                    elif mode == "pthreads":
                        chunk_results_df = run_pthreads(chunk_df, key_df['correct_answer'], scoring_rules)
                    else:
                        logger.log("ERROR", "validation", f"Modo de ejecución no válido: {mode}", extra={"rule_id": "RF-02", "mode_attempted": mode})
                        return {"status": "error", "message": "Modo de ejecución no válido."}
                    all_results_list.append(chunk_results_df)

                results_df = pd.concat(all_results_list, ignore_index=True)
            else:
                if mode == "serial":
                    results_df = run_serial(students_df, key_df['correct_answer'], scoring_rules)
                elif mode == "openmp":
                    results_df = run_openmp(students_df, key_df['correct_answer'], scoring_rules)
                elif mode == "cuda":
                    results_df = run_cuda(students_df, key_df['correct_answer'], scoring_rules)
                elif mode == "pthreads":
                    results_df = run_pthreads(students_df, key_df['correct_answer'], scoring_rules)
                else:
                    logger.log("ERROR", "validation", f"Modo de ejecución no válido: {mode}", extra={"rule_id": "RF-02", "mode_attempted": mode})
                    return {"status": "error", "message": "Modo de ejecución no válido."}

            # Convertir resultados a formato JSON para la respuesta
            results_json = results_df.to_dict(orient='records')
            metrics = {
                "total_students": len(results_df),
                "average_score": results_df['score'].mean(),
                "average_correct": results_df['correct'].mean(),
                "average_wrong": results_df['wrong'].mean(),
                "average_blank": results_df['blank'].mean(),
            }
            logger.log("INFO", "execution", "Evaluación completada exitosamente.", extra={"mode": mode, "metrics": metrics, "rule_ids": ["RF-05", "RF-08"]})
            
            # Ejecutar el benchmark completo en segundo plano
            try:
                modes_to_run = ['serial', mode] if mode != 'serial' else ['serial']
                run_full_benchmark(students_df, key_df['correct_answer'], scoring_rules, modes_to_run=modes_to_run)
                logger.log("INFO", "benchmark", "Benchmark ejecutado y resultados actualizados.")
            except Exception as e_benchmark:
                logger.log("ERROR", "benchmark", f"Error al ejecutar el benchmark: {str(e_benchmark)}", extra={"error_details": str(e_benchmark)})

            return {"status": "ok", "results": results_json, "metrics": metrics}
        except Exception as e:
            logger.log("ERROR", "execution", f"Error durante la evaluación: {str(e)}", extra={"error_details": str(e), "rule_id": "RF-08"})
            return {"status": "error", "message": str(e)}

    @app.get("/logs/list")
    async def list_logs():
        log_dir = "logs"
        dates = []
        files_by_date = {}

        if not os.path.exists(log_dir):
            return {"dates": dates, "files": files_by_date}

        for date_dir in os.listdir(log_dir):
            full_date_path = os.path.join(log_dir, date_dir)
            if os.path.isdir(full_date_path):
                try:
                    # Validate date format (YYYY-MM-DD)
                    datetime.strptime(date_dir, "%Y-%m-%d")
                    dates.append(date_dir)
                    files_by_date[date_dir] = []
                    for log_file in os.listdir(full_date_path):
                        if log_file.endswith(".jsonl"):
                            files_by_date[date_dir].append(log_file)
                    files_by_date[date_dir].sort()
                except ValueError:
                    # Ignore directories that are not in YYYY-MM-DD format
                    continue
        dates.sort(reverse=True) # Sort dates in descending order
        return {"dates": dates, "files": files_by_date}

    @app.get("/logs/download/{date}/{filename}")
    async def download_log(date: str, filename: str, format: str = None):
        log_filepath = os.path.join("logs", date, filename)

        if not os.path.exists(log_filepath):
            logger.log("ERROR", "log_download", f"Archivo de log no encontrado: {log_filepath}", extra={"date": date, "filename": filename})
            return {"status": "error", "message": "Archivo no encontrado."}, 404
        
        if format == "csv":
            try:
                records = []
                with open(log_filepath, 'r', encoding='utf-8') as f:
                    for line in f:
                        records.append(json.loads(line))
                
                if not records:
                    return StreamingResponse(io.StringIO(""), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename.replace('.jsonl', '.csv')}"})

                df = pd.DataFrame.from_records(records)
                
                # Flatten 'extra' column if it exists and contains dictionaries
                if 'extra' in df.columns and any(isinstance(x, dict) for x in df['extra'].dropna()):
                    extra_df = pd.json_normalize(df['extra'])
                    df = pd.concat([df.drop(columns=['extra']), extra_df], axis=1)

                output = io.StringIO()
                df.to_csv(output, index=False)
                output.seek(0)
                logger.log("INFO", "log_download", f"Log convertido y descargado como CSV: {log_filepath}", extra={"date": date, "filename": filename, "format": "csv"})
                return StreamingResponse(io.StringIO(output.getvalue()), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename.replace('.jsonl', '.csv')}"})
            except Exception as e:
                logger.log("ERROR", "log_download", f"Error al convertir log a CSV: {log_filepath} - {str(e)}", extra={"date": date, "filename": filename, "error_details": str(e)})
                return {"status": "error", "message": f"Error al convertir a CSV: {str(e)}"}, 500
        else:
            logger.log("INFO", "log_download", f"Log descargado: {log_filepath}", extra={"date": date, "filename": filename})
            return FileResponse(log_filepath, media_type="application/jsonl", filename=filename)

    @app.get("/benchmark/data")
    async def get_benchmark_data():
        try:
            df = pd.read_csv("data/benchmark_summary.csv")
            return {"status": "ok", "data": df.to_dict(orient='records')}
        except FileNotFoundError:
            logger.log("ERROR", "benchmark_data", "Archivo data/benchmark_summary.csv no encontrado.")
            return {"status": "error", "message": "Archivo data/benchmark_summary.csv no encontrado."}, 404
        except Exception as e:
            logger.log("ERROR", "benchmark_data", f"Error al leer benchmark.csv: {str(e)}")
            return {"status": "error", "message": f"Error al leer benchmark.csv: {str(e)}"}, 500

    @app.get("/output/benchmark_plot.html")
    async def get_benchmark_plot():
        plot_path = "output/benchmark_plot.html"
        if not os.path.exists(plot_path):
            logger.log("ERROR", "benchmark_plot", f"Archivo {plot_path} no encontrado.")
            return {"status": "error", "message": f"Archivo {plot_path} no encontrado."}, 404
        return FileResponse(plot_path, media_type="text/html")