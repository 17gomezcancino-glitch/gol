"""Herramientas de análisis y afinación para audio.

Incluye:
* Afinador de guitarra en tiempo real mediante micrófono.
* Detección heurística de instrumento (guitarra u otro).
* Reconocimiento de género musical básico.
* Estimación de la tonalidad (escala mayor o menor).
"""

import argparse
from typing import Tuple

import librosa
import numpy as np
import sounddevice as sd

STANDARD_TUNING = {
    "E2": 82.41,
    "A2": 110.00,
    "D3": 146.83,
    "G3": 196.00,
    "B3": 246.94,
    "E4": 329.63,
}


MAJOR_PROFILE = np.array(
    [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
)
MINOR_PROFILE = np.array(
    [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
)
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def detect_frequency(samples: np.ndarray, samplerate: int) -> float:
    """Return the dominant frequency in the given audio samples."""
    window = np.hanning(len(samples))
    spectrum = np.fft.rfft(samples * window)
    frequencies = np.fft.rfftfreq(len(samples), d=1 / samplerate)
    peak = np.argmax(np.abs(spectrum))
    return float(frequencies[peak])


def classify_instrument(y: np.ndarray, sr: int) -> str:
    """Heurísticamente determina si el audio corresponde a una guitarra."""
    zcr = float(librosa.feature.zero_crossing_rate(y).mean())
    centroid = float(librosa.feature.spectral_centroid(y=y, sr=sr).mean())
    if centroid < 2000 and zcr < 0.1:
        return "guitarra"
    return "otro instrumento"


def classify_genre(y: np.ndarray, sr: int) -> str:
    """Clasificación de género musical muy básica basada en tempo."""
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    if tempo > 100:
        return "rock"
    return "clásica"


def detect_scale(y: np.ndarray, sr: int) -> str:
    """Estima la tonalidad utilizando perfiles de pitch class."""
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr).mean(axis=1)
    best_key: Tuple[str, float] = ("Desconocida", -np.inf)
    for i in range(12):
        maj_score = np.corrcoef(np.roll(MAJOR_PROFILE, i), chroma)[0, 1]
        min_score = np.corrcoef(np.roll(MINOR_PROFILE, i), chroma)[0, 1]
        if maj_score > best_key[1]:
            best_key = (f"{NOTE_NAMES[i]} mayor", maj_score)
        if min_score > best_key[1]:
            best_key = (f"{NOTE_NAMES[i]} menor", min_score)
    return best_key[0]


def tune(duration: float, samplerate: int) -> None:
    """Loop de afinación de guitarra."""
    print("Presiona Ctrl+C para salir.")
    try:
        while True:
            frames = int(duration * samplerate)
            audio = sd.rec(frames, samplerate=samplerate, channels=1, dtype="float64")
            sd.wait()
            frequency = detect_frequency(audio[:, 0], samplerate)
            string, target = min(
                STANDARD_TUNING.items(), key=lambda item: abs(item[1] - frequency)
            )
            diff = frequency - target
            if diff > 1:
                direction = "baja"
            elif diff < -1:
                direction = "sube"
            else:
                direction = "afinada"
            print(f"{string}: {frequency:.2f} Hz ({diff:+.2f} Hz) -> {direction}")
    except KeyboardInterrupt:
        print("\nHasta luego!")


def analyze(filepath: str) -> None:
    """Analiza un archivo de audio e imprime sus características."""
    y, sr = librosa.load(filepath)
    instrument = classify_instrument(y, sr)
    genre = classify_genre(y, sr)
    scale = detect_scale(y, sr)
    print(f"Instrumento: {instrument}")
    print(f"Género: {genre}")
    print(f"Tonalidad: {scale}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Herramientas de audio")
    sub = parser.add_subparsers(dest="command", required=True)

    tune_p = sub.add_parser("tune", help="Afinador de guitarra")
    tune_p.add_argument("--duration", type=float, default=0.5, help="Duración de cada muestra en segundos")
    tune_p.add_argument("--samplerate", type=int, default=44100, help="Frecuencia de muestreo en Hz")

    analyze_p = sub.add_parser("analyze", help="Analiza un archivo de audio")
    analyze_p.add_argument("filepath", help="Ruta del archivo de audio a analizar")

    args = parser.parse_args()

    if args.command == "tune":
        tune(args.duration, args.samplerate)
    else:
        analyze(args.filepath)


if __name__ == "__main__":
    main()
