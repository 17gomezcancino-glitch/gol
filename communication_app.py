"""Cross-platform communication app leveraging Google account authentication.

This module defines a Flet-based application that allows users to authenticate
with their Google account and converse with an AI agent using the OpenAI API.

The app is designed to work across desktop (Windows, Linux, macOS) and mobile
platforms (iOS, Android) thanks to Flet's deployment options. Authentication is
performed through Google's OAuth 2.0 installed application flow, which is
suitable for a variety of environments. Once authenticated, the app displays the
user profile information returned by Google and unlocks a chat interface where
messages can be exchanged with the AI agent.

The implementation deliberately keeps the chat logic modular so it can be
replaced by any backend agent. By default, it uses the OpenAI Chat Completions
API if the `openai` package is installed and a valid API key is supplied via the
`OPENAI_API_KEY` environment variable or command-line argument. If the
requirements are not met, the agent falls back to a simple echo bot, ensuring
that the user interface remains functional.
"""

from __future__ import annotations

import argparse
import math
import threading
from pathlib import Path
from typing import List, Optional

import flet as ft
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from chat_models import AgentResponse, ChatMessage
from conversation_history import ConversationHistory
from input_controller import InputController

try:  # pragma: no-cover - optional dependency
    from openai import OpenAI
except ImportError:  # pragma: no-cover - optional dependency
    OpenAI = None  # type: ignore

GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
]
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"


class AuthenticationError(RuntimeError):
    """Raised when Google authentication fails."""


class AgentClient:
    """Simple abstraction over the communication agent backend."""

    def __init__(self, api_key: Optional[str], model: str = "gpt-3.5-turbo") -> None:
        self._api_key = api_key or ""
        self._model = model
        self._client = None
        if OpenAI is not None and self._api_key:
            self._client = OpenAI(api_key=self._api_key)

    def is_configured(self) -> bool:
        return self._client is not None

    def send(self, messages: List[ChatMessage]) -> AgentResponse:
        """Send the conversation to the backend and return the agent response."""

        if self._client is None:
            # Fallback to a simple echo bot for demonstration purposes.
            reply_content = (
                "(Modo demo) Has dicho: " + messages[-1].content
                if messages
                else "Hola, ¿en qué puedo ayudarte?"
            )
            return AgentResponse(ChatMessage("Agente", reply_content), metadata={"mode": "demo"})

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user" if m.author == "Usuario" else "assistant", "content": m.content} for m in messages],
        )
        choice = response.choices[0]
        content = choice.message.content or ""
        metadata = {
            "model": response.model,
            "finish_reason": choice.finish_reason,
            "usage": response.usage.model_dump() if hasattr(response.usage, "model_dump") else None,
        }
        return AgentResponse(ChatMessage("Agente", content), metadata=metadata)
class GoogleSession:
    """Handles Google OAuth session management."""

    def __init__(self, client_secrets: Path, token_storage: Path, scopes: List[str]) -> None:
        self._client_secrets = client_secrets
        self._token_storage = token_storage
        self._scopes = scopes
        self._credentials: Optional[Credentials] = None

    def authenticate(self) -> dict:
        """Authenticate with Google and return the user information."""

        creds = self._load_credentials()
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self._client_secrets), scopes=self._scopes
                )
                try:
                    creds = flow.run_local_server(port=0)
                except OSError:
                    # Fallback for environments where opening a local server is not possible.
                    creds = flow.run_console()

            self._save_credentials(creds)

        userinfo = self._fetch_userinfo(creds)
        self._credentials = creds
        return userinfo

    def logout(self) -> None:
        if self._token_storage.exists():
            self._token_storage.unlink()
        self._credentials = None

    def _load_credentials(self) -> Optional[Credentials]:
        if not self._token_storage.exists():
            return None
        creds = Credentials.from_authorized_user_file(str(self._token_storage), self._scopes)
        return creds

    def _save_credentials(self, creds: Credentials) -> None:
        self._token_storage.parent.mkdir(parents=True, exist_ok=True)
        with self._token_storage.open("w", encoding="utf-8") as fh:
            fh.write(creds.to_json())

    def _fetch_userinfo(self, creds: Credentials) -> dict:
        response = requests.get(
            GOOGLE_USERINFO_ENDPOINT,
            headers={"Authorization": f"Bearer {creds.token}"},
            timeout=10,
        )
        if response.status_code != 200:
            raise AuthenticationError(
                f"No se pudo obtener la información del perfil (HTTP {response.status_code})."
            )
        return response.json()


class CommunicationApp:
    """Main application controller for the communication experience."""

    def __init__(
        self,
        page: ft.Page,
        google_session: GoogleSession,
        agent_client: AgentClient,
        history_manager: ConversationHistory,
    ) -> None:
        self.page = page
        self.google_session = google_session
        self.agent_client = agent_client
        self.history_manager = history_manager
        self.input_controller = InputController()
        self.userinfo: Optional[dict] = None
        self.messages: List[ChatMessage] = []
        self.current_user_id: Optional[str] = None

        self.page.title = "Agente Multiplataforma"
        self.page.window_width = 420
        self.page.window_height = 780
        self.page.vertical_alignment = ft.MainAxisAlignment.START

        self.status_text = ft.Text("Inicia sesión con Google para comenzar.")
        self.login_button = ft.ElevatedButton("Iniciar sesión con Google", on_click=self._handle_login)
        self.logout_button = ft.ElevatedButton("Cerrar sesión", visible=False, on_click=self._handle_logout)

        self.history_status = ft.Text("", size=12, color=ft.colors.GREY, visible=False)
        self.export_button = ft.IconButton(
            ft.icons.SAVE_ALT,
            tooltip="Exportar historial a Markdown",
            visible=False,
            on_click=self._handle_export_history,
        )
        self.clear_button = ft.IconButton(
            ft.icons.DELETE_SWEEP,
            tooltip="Borrar historial",
            visible=False,
            on_click=self._handle_clear_history,
        )
        self.history_toolbar = ft.Row(
            [
                ft.Text("Historial de chat", weight=ft.FontWeight.BOLD),
                ft.Row([self.export_button, self.clear_button]),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            visible=False,
        )

        self.chat_list = ft.ListView(expand=True, spacing=10, padding=10, auto_scroll=True)
        self.input_field = ft.TextField(hint_text="Escribe tu mensaje", expand=True, on_submit=self._handle_send)
        self.send_button = ft.IconButton(ft.icons.SEND, on_click=self._handle_send)
        self.chat_row = ft.Row([self.input_field, self.send_button], visible=False)

        self.remote_panel = self._build_remote_panel()

        self.page.add(
            ft.Column(
                [
                    ft.Row([self.status_text], alignment=ft.MainAxisAlignment.START),
                    ft.Row([self.login_button, self.logout_button]),
                    self.history_toolbar,
                    self.history_status,
                    self.chat_list,
                    self.chat_row,
                    self.remote_panel,
                ],
                expand=True,
            )
        )

    def _handle_login(self, _event: ft.ControlEvent) -> None:
        self.status_text.value = "Autenticando con Google..."
        self.page.update()
        threading.Thread(target=self._authenticate_user, daemon=True).start()

    def _authenticate_user(self) -> None:
        try:
            userinfo = self.google_session.authenticate()
        except Exception as exc:  # pragma: no-cover - UI feedback only
            self._update_status(f"Error de autenticación: {exc}")
            return

        self.userinfo = userinfo
        self.current_user_id = userinfo.get("sub") or userinfo.get("email") or "usuario"
        display_name = userinfo.get("name") or userinfo.get("email") or "Usuario"
        self._update_status(f"Sesión iniciada como {display_name}")
        self.page.call_later(self._enable_chat)

    def _enable_chat(self) -> None:
        self.login_button.visible = False
        self.logout_button.visible = True
        self.chat_row.visible = True
        self.history_toolbar.visible = True
        self.history_status.visible = True
        self.export_button.visible = True
        self.clear_button.visible = True
        if self.remote_panel is not None:
            self.remote_panel.visible = True
        self._load_previous_messages()
        self.page.update()

    def _update_status(self, message: str) -> None:
        self.status_text.value = message
        self.page.update()

    def _handle_logout(self, _event: ft.ControlEvent) -> None:
        self.google_session.logout()
        self.userinfo = None
        self.current_user_id = None
        self.messages.clear()
        self.chat_list.controls.clear()
        self.login_button.visible = True
        self.logout_button.visible = False
        self.chat_row.visible = False
        self.history_toolbar.visible = False
        self.history_status.visible = False
        self.history_status.value = ""
        self.export_button.visible = False
        self.clear_button.visible = False
        if self.remote_panel is not None:
            self.remote_panel.visible = False
        self.status_text.value = "Sesión finalizada."
        self.page.update()

    def _handle_send(self, _event: ft.ControlEvent) -> None:
        content = self.input_field.value.strip()
        if not content:
            return
        self.input_field.value = ""
        user_display = self.userinfo.get("given_name") if self.userinfo else "Usuario"
        user_message = ChatMessage(user_display or "Usuario", content)
        self.messages.append(user_message)
        self._add_message_to_view(user_message)
        self._persist_history()
        self.page.update()
        threading.Thread(target=self._request_agent_response, daemon=True).start()

    def _request_agent_response(self) -> None:
        response = self.agent_client.send(self.messages)
        self.messages.append(response.message)
        self.page.call_later(lambda: self._handle_agent_message(response.message))

    def _handle_agent_message(self, message: ChatMessage) -> None:
        self._add_message_to_view(message)
        self._persist_history()
        self.page.update()

    def _add_message_to_view(self, message: ChatMessage, update_page: bool = True) -> None:
        bubble = ft.Container(
            content=ft.Text(message.content),
            bgcolor=ft.colors.BLUE_100 if message.author != "Agente" else ft.colors.GREEN_100,
            padding=10,
            border_radius=10,
            alignment=ft.alignment.center_left if message.author != "Agente" else ft.alignment.center_right,
        )
        self.chat_list.controls.append(bubble)
        if update_page:
            self.page.update()

    def _load_previous_messages(self) -> None:
        if not self.current_user_id:
            return
        previous_messages = self.history_manager.load(self.current_user_id)
        self.chat_list.controls.clear()
        if not previous_messages:
            self.messages = []
            self.history_status.value = "Comienza una nueva conversación."
            return
        self.messages = list(previous_messages)
        for message in self.messages:
            self._add_message_to_view(message, update_page=False)
        self.history_status.value = f"Historial cargado ({len(self.messages)} mensajes)."

    def _persist_history(self) -> None:
        if not self.current_user_id:
            return
        path = self.history_manager.save(self.current_user_id, self.messages)
        self.history_status.value = f"Historial guardado en {path}."

    def _handle_export_history(self, _event: ft.ControlEvent) -> None:
        if not self.current_user_id:
            return
        export_path = self.history_manager.export_markdown(self.current_user_id, self.messages)
        self.history_status.value = f"Historial exportado a {export_path}."
        self.page.update()

    def _handle_clear_history(self, _event: ft.ControlEvent) -> None:
        if not self.current_user_id:
            return
        self.history_manager.clear(self.current_user_id)
        self.messages.clear()
        self.chat_list.controls.clear()
        self.history_status.value = "Historial eliminado."
        self.page.update()

    def _build_remote_panel(self) -> ft.Control:
        if not self.input_controller.available:
            return ft.Column(
                [
                    ft.Text(
                        "Control remoto no disponible en este dispositivo.",
                        color=ft.colors.GREY,
                    )
                ],
                visible=False,
            )

        self.trackpad_feedback = ft.Text("Desliza para mover el cursor", size=12)
        self.sensitivity_slider = ft.Slider(
            min=0.5,
            max=5.0,
            divisions=9,
            value=self.input_controller.sensitivity,
            label="{value}x",
            on_change=self._handle_sensitivity_change,
        )

        trackpad_surface = ft.Container(
            width=280,
            height=280,
            bgcolor=ft.colors.BLUE_GREY_50,
            border_radius=ft.border_radius.all(16),
        )
        gesture_detector = ft.GestureDetector(
            content=trackpad_surface,
            on_pan_update=self._handle_trackpad_pan,
        )

        click_row = ft.Row(
            [
                ft.ElevatedButton("Click izquierdo", on_click=lambda _: self.input_controller.click("left")),
                ft.ElevatedButton("Click derecho", on_click=lambda _: self.input_controller.click("right")),
            ],
            alignment=ft.MainAxisAlignment.SPACE_EVENLY,
        )

        self.keyboard_field = ft.TextField(
            hint_text="Escribe texto para enviar al equipo",
            on_submit=self._handle_keyboard_submit,
        )
        send_keyboard_button = ft.IconButton(ft.icons.KEYBOARD, on_click=self._handle_keyboard_submit)

        keyboard_row = ft.Row([self.keyboard_field, send_keyboard_button])

        return ft.Column(
            [
                ft.Text("Control remoto"),
                self.trackpad_feedback,
                gesture_detector,
                ft.Text("Sensibilidad del cursor"),
                self.sensitivity_slider,
                click_row,
                keyboard_row,
            ],
            spacing=10,
            visible=False,
        )

    def _handle_trackpad_pan(self, event: ft.DragUpdateEvent) -> None:
        if not self.input_controller.available:
            return
        delta_x = event.delta_x or 0
        delta_y = event.delta_y or 0
        magnitude = math.hypot(delta_x, delta_y)
        if magnitude == 0:
            return
        self.trackpad_feedback.value = f"Movimiento: Δx={delta_x:.1f}, Δy={delta_y:.1f}"
        self.input_controller.move_pointer(delta_x, delta_y)
        self.page.update()

    def _handle_sensitivity_change(self, event: ft.ControlEvent) -> None:
        try:
            value = float(event.control.value)
        except (TypeError, ValueError):
            value = 1.0
        self.input_controller.update_sensitivity(value)
        self.page.update()

    def _handle_keyboard_submit(self, _event: ft.ControlEvent) -> None:
        text = self.keyboard_field.value
        if not text:
            return
        self.input_controller.type_text(text)
        self.keyboard_field.value = ""
        self.trackpad_feedback.value = f"Texto enviado: {text}"
        self.page.update()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aplicación de comunicación con autenticación de Google.")
    parser.add_argument(
        "--client-secrets",
        required=True,
        type=Path,
        help="Ruta al archivo client_secrets.json descargado desde la consola de Google Cloud.",
    )
    parser.add_argument(
        "--token-file",
        default=Path.home() / ".config" / "gol" / "communication_app_tokens.json",
        type=Path,
        help="Ruta donde se guardará el token de actualización de Google.",
    )
    parser.add_argument(
        "--openai-api-key",
        default=None,
        help="Clave de API de OpenAI para habilitar el agente inteligente (opcional).",
    )
    parser.add_argument(
        "--model",
        default="gpt-3.5-turbo",
        help="Modelo de OpenAI a utilizar para las respuestas del agente.",
    )
    parser.add_argument(
        "--history-dir",
        default=Path.home() / ".config" / "gol" / "chat_histories",
        type=Path,
        help="Directorio donde se guardarán los historiales de chat.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    google_session = GoogleSession(
        client_secrets=args.client_secrets,
        token_storage=args.token_file,
        scopes=GOOGLE_SCOPES,
    )

    agent_client = AgentClient(api_key=args.openai_api_key, model=args.model)
    history_manager = ConversationHistory(args.history_dir)

    def app(page: ft.Page) -> None:
        CommunicationApp(page, google_session, agent_client, history_manager)

    ft.app(target=app)


if __name__ == "__main__":
    main()
