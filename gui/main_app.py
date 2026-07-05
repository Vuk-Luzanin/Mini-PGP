"""
gui/main_app.py

Glavna Kivy aplikacija - sadrži navigaciju (TabbedPanel) između:
  - Upravljanje ključevima (prsten javnih/privatnih ključeva)
  - Slanje poruke
  - Prijem poruke
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label

from storage.keyring import KeyRing
from core.key_manager import KeyManager
from core.pgp_engine import PGPEngine

from gui.key_management_screen import KeyManagementScreen
from gui.send_message_screen import SendMessageScreen
from gui.receive_message_screen import ReceiveMessageScreen


class PGPApp(App):
    title = "PGP Aplikacija — Zaštita podataka"

    def build(self):
        # ----- Inicijalizacija "backend" objekata -----
        self.keyring = KeyRing()
        self.key_manager = KeyManager(self.keyring)
        self.pgp_engine = PGPEngine(self.key_manager)

        root = BoxLayout(orientation="vertical")

        header = Label(
            text="PGP — Pretty Good Privacy (skeleton aplikacija)",
            size_hint_y=None,
            height=40,
            bold=True,
        )
        root.add_widget(header)

        # navigation tabs
        tabs = TabbedPanel(do_default_tab=False)

        key_tab = TabbedPanelItem(text="Ključevi")
        self.key_management_screen = KeyManagementScreen(self.key_manager)
        key_tab.add_widget(self.key_management_screen)
        tabs.add_widget(key_tab)

        send_tab = TabbedPanelItem(text="Slanje poruke")
        self.send_screen = SendMessageScreen(self.key_manager, self.pgp_engine)
        send_tab.add_widget(self.send_screen)
        tabs.add_widget(send_tab)

        receive_tab = TabbedPanelItem(text="Prijem poruke")
        self.receive_screen = ReceiveMessageScreen(self.key_manager, self.pgp_engine)
        receive_tab.add_widget(self.receive_screen)
        tabs.add_widget(receive_tab)

        # kad se promeni tab, pozovi self._on_tab_changed
        # ako je otvoren tab Kljucevi, onda current_tab pokazuje na key_tab
        tabs.bind(current_tab=self._on_tab_changed)
        self._tabs = tabs                           # save reference to tabs for later use
        self._send_tab = send_tab

        root.add_widget(tabs)
        return root

    def _on_tab_changed(self, instance, value):
        # Ako je otvoren tab Slanje poruke, osveži listu kljuceva u tom tabu
        if value is self._send_tab:
            self.send_screen.refresh_key_lists()

        if hasattr(self, "key_management_screen"):
            self.key_management_screen.refresh()
