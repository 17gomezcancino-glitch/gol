"""Prototype AR assistant that overlays tutorial steps on a webcam feed.

Por defecto, el asistente explica el editor de nodos de Blender, aunque acepta
cualquier tema como argumento. También es experto en FL Studio y puede guiarte
para crear una canción desde cero.
"""

import cv2
import openai

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
    parser.add_argument(
        "--mute",
        action="store_true",
        help="Disable voice output",
    )
    args = parser.parse_args()

    assistant = AITutorialAssistant(api_key=args.api_key)
    cap = cv2.VideoCapture(0)
    step = 1
    instruction = assistant.get_step(args.topic, step)
    engine = None
    if not args.mute:
        try:
            import pyttsx3
        except ImportError as exc:
            raise SystemExit(
                "pyttsx3 is required for voice output. Install it with `pip install pyttsx3`."
            ) from exc
        engine = pyttsx3.init()
        engine.say(instruction)
        engine.runAndWait()

    if not cap.isOpened():
        raise SystemExit("Could not open webcam")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cv2.putText(
                frame,
                instruction,
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            cv2.imshow("Tutorial", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("n"):
                step += 1
                instruction = assistant.get_step(args.topic, step)
                if engine:
                    engine.say(instruction)
                    engine.runAndWait()
            elif key == ord("q"):
                break
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
