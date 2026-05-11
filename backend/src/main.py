# backend/src/main.py
import os
import sys
import uuid

from backend.src.domain.entities import TranscriptionJob
from backend.src.infrastructure.dependency_injection import create_transcription_service
from backend.src.config import AVAILABLE_MODES


def mostrar_ayuda():
    print("\n=== TranscriberApp ===")
    print("Procesa audios (.mp3, .webm) o textos (.txt) y genera resúmenes con distintos modos.\n")

    print("USO:")
    print("  python -m transcriber_app.main [audio|texto] [nombre] [modo]\n")

    print("PARÁMETROS:")
    print("  audio        Procesa un archivo .mp3 o .webm desde la carpeta 'audios/'")
    print("  texto        Procesa un archivo .txt desde la carpeta 'transcripts/'")
    print("  nombre       Nombre del archivo SIN extensión")
    print("  modo         Tipo de resumen a generar\n")

    print("MODOS DISPONIBLES:")
    for m in AVAILABLE_MODES:
        print(f"  - {m}")
    print()

    print("EJEMPLOS:")
    print("  Procesar audio:")
    print("    python -m transcriber_app.main audio reunion1 tecnico")
    print("    (usa audios/reunion1.mp3)\n")

    print("  Procesar texto:")
    print("    python -m transcriber_app.main texto sprint1 refinamiento")
    print("    (usa transcripts/sprint1.txt)\n")

    print("SALIDA:")
    print("  - La transcripción (si es audio) se guarda en: transcripts/<nombre>.txt")
    print("  - El resumen final se guarda en: outputs/<nombre>_<modo>.md\n")


def main():

    # ============================
    #   VALIDACIÓN DE ARGUMENTOS
    # ============================
    if len(sys.argv) < 4:
        mostrar_ayuda()
        return

    input_type = sys.argv[1].lower()
    base_name = sys.argv[2]
    mode = sys.argv[3].lower()

    if mode not in AVAILABLE_MODES:
        print(f"❌ Modo no válido: {mode}\n")
        mostrar_ayuda()
        return

    # ============================
    #   RESOLVER RUTA SEGÚN TIPO
    # ============================
    if input_type == "audio":
        # Intentar encontrar el archivo con extensiones comunes
        path = None
        for ext in [".mp3", ".webm", ".wav"]:
            test_path = os.path.join("audios", base_name if base_name.endswith(ext) else base_name + ext)
            if os.path.exists(test_path):
                path = test_path
                break

        if not path:
            # Fallback a .mp3 para el mensaje de error si no existe nada
            path = os.path.join("audios", base_name if base_name.endswith(".mp3") else base_name + ".mp3")

    elif input_type == "texto":
        if not base_name.endswith(".txt"):
            base_name += ".txt"
        path = os.path.join("transcripts", base_name)

    else:
        print("❌ Primer parámetro debe ser 'audio' o 'texto'\n")
        mostrar_ayuda()
        return

    if not os.path.exists(path):
        print(f"❌ No existe el archivo: {path}\n")
        return

    # ============================
    #   INICIALIZAR PIPELINE (Hexagonal Architecture)
    # ============================
    service = create_transcription_service()

    # ============================
    #   EJECUTAR PIPELINE
    # ============================
    try:
        job_id = str(uuid.uuid4())
        job = TranscriptionJob(
            job_id=job_id,
            audio_path=path,
            audio_filename=os.path.basename(path),
            mode=mode,
        )

        if input_type == "audio":
            result = service.process_audio(job)
            output = f"✅ Transcripción guardada: {result.transcription_text[:100]}...\n✅ Resumen guardado en: {result.output_file_path}"
        else:
            # For text input, read the file and process
            with open(path, "r", encoding="utf-8") as f:
                text_content = f.read()
            result = service.process_text(job, text_content)
            output = f"✅ Texto procesado: {text_content[:100]}...\n✅ Resumen guardado en: {result.output_file_path}"

    except ValueError as e:
        print(f"[BAD_AUDIO] {e}")
        sys.exit(3)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    print(output)


if __name__ == "__main__":
    main()
