"""Prototype AR assistant that overlays tutorial steps on a webcam feed.

Por defecto, el asistente explica el editor de nodos de Blender, aunque acepta
cualquier tema como argumento. También es experto en FL Studio y puede guiarte
para crear una canción desde cero.
"""

import time

import cv2
import openai
import requests

class AITutorialAssistant:
    """Simple assistant that fetches tutorial steps via the OpenAI API."""
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        openai.api_key = api_key
        self.model = model

    def get_step(self, topic: str, step: int) -> str:
        """Return text for a step-by-step tutorial."""
        prompt = (
            f"You are teaching a user how to use {topic}. "
            f"Provide concise instructions for step {step}."
        )
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message["content"].strip()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AR Tutorial Assistant")
    parser.add_argument(
        "topic",
        nargs="?",
        default="Blender node editor",
        help="Program or topic to learn (default: Blender node editor)",
    )
    parser.add_argument("--api-key", required=True, help="OpenAI API key")
    args = parser.parse_args()

    assistant = AITutorialAssistant(api_key=args.api_key)
    cap = cv2.VideoCapture(0)
    step = 1
    max_attempts = 3

    if not cap.isOpened():
        raise SystemExit("Could not open webcam")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            success = False
            color = (0, 255, 0)
            for attempt in range(1, max_attempts + 1):
                try:
                    instruction = assistant.get_step(args.topic, step)
                    success = True
                    break
                except (
                    openai.error.OpenAIError,
                    requests.exceptions.RequestException,
                ) as exc:
                    wait_time = 2 ** attempt
                    print(
                        f"Error obteniendo el paso (intento {attempt}/{max_attempts}): {exc}."
                    )
                    time.sleep(wait_time)
            else:
                instruction = (
                    "No se pudieron obtener instrucciones. "
                    "Presiona 'n' para reintentar."
                )
                color = (0, 0, 255)
                print(instruction)
            cv2.putText(
                frame,
                instruction,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                color,
                2,
                cv2.LINE_AA,
            )
            cv2.imshow("Tutorial", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("n"):
                if success:
                    step += 1
            elif key == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
