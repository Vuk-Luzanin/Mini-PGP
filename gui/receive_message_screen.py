"""
gui/receive_message_screen.py

Ekran za prijem poruke: izbor datoteke, dekripcija i verifikacija,
prikaz informacija o uspešnosti i autoru potpisa, te čuvanje
originalne poruke.
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

from gui.message_popup import show_message, show_password_prompt
from gui.file_chooser_popup import show_open_file_popup, show_save_file_popup


class ReceiveMessageScreen(BoxLayout):
    def __init__(self, key_manager, pgp_engine, **kwargs):
        super().__init__(orientation="vertical", padding=8, spacing=8, **kwargs)
        self.key_manager = key_manager
        self.pgp_engine = pgp_engine
        self.last_plaintext = None
        self.selected_path = None

        # ----- Izbor fajla -----
        top_row = BoxLayout(size_hint_y=None, height=42, spacing=8)
        top_row.add_widget(Label(text="Datoteka:", size_hint_x=0.2))
        self.path_label = Label(text="(nije izabrana)", size_hint_x=0.5, halign="left", valign="middle")
        top_row.add_widget(self.path_label)
        choose_btn = Button(text="Izaberi...", size_hint_x=0.15)
        choose_btn.bind(on_release=lambda *_: self._browse_file())
        top_row.add_widget(choose_btn)
        process_btn = Button(text="Obradi", size_hint_x=0.15)
        process_btn.bind(on_release=lambda *_: self._on_process())
        top_row.add_widget(process_btn)
        self.add_widget(top_row)

        # ----- Informacije -----
        info_box = GridLayout(cols=2, size_hint_y=None, spacing=4)
        info_box.bind(minimum_height=info_box.setter("height"))

        self.status_label = Label(text="—")
        self.signature_label = Label(text="—")
        self.signer_label = Label(text="—")
        self.encrypted_label = Label(text="—")
        self.compressed_label = Label(text="—")
        self.radix64_label = Label(text="—")

        rows = [
            ("Status obrade:", self.status_label),
            ("Provera potpisa:", self.signature_label),
            ("Autor potpisa:", self.signer_label),
            ("Bilo enkriptovano:", self.encrypted_label),
            ("Bilo komprimovano:", self.compressed_label),
            ("Radix-64:", self.radix64_label),
        ]
        for text, label in rows:
            info_box.add_widget(Label(text=text, size_hint_y=None, height=26))
            label.size_hint_y = None
            label.height = 26
            info_box.add_widget(label)

        self.add_widget(info_box)

        # ----- Prikaz poruke -----
        self.add_widget(Label(text="Dekriptovana poruka:", bold=True, size_hint_y=None, height=24))
        self.message_display = TextInput(readonly=True, multiline=True)
        self.add_widget(self.message_display)

        save_btn = Button(text="Sačuvaj originalnu poruku...", size_hint_y=None, height=42)
        save_btn.bind(on_release=lambda *_: self._on_save_message())
        self.add_widget(save_btn)

    def _browse_file(self):
        def _selected(path):
            self.selected_path = path
            self.path_label.text = path

        show_open_file_popup(on_selected=_selected, title="Izaberite PGP datoteku", filters=["*.pgp", "*.*"])

    def _on_process(self):
        if not self.selected_path:
            show_message("Upozorenje", "Izaberite datoteku poruke.")
            return

        def _with_password(password):
            try:
                result = self.pgp_engine.receive_message(self.selected_path, password)
            except NotImplementedError:
                show_message(
                    "Nije implementirano",
                    "Prijem poruke još nije implementiran (core/pgp_engine.py)."
                )
                return
            except Exception as e:
                show_message("Greška", f"Obrada poruke nije uspela:\n{e}")
                return
            self._display_result(result)

        show_password_prompt(
            "Unesite lozinku privatnog ključa (ako je poruka enkriptovana):",
            on_submit=_with_password
        )

    def _display_result(self, result):
        if not result.success:
            self.status_label.text = "GREŠKA"
            show_message("Greška", result.error_message or "Nepoznata greška prilikom obrade poruke.")
            self.message_display.text = ""
            self.last_plaintext = None
            return

        self.status_label.text = "Uspešno"
        self.encrypted_label.text = "Da" if result.was_encrypted else "Ne"
        self.compressed_label.text = "Da" if result.was_compressed else "Ne"
        self.radix64_label.text = "Da" if result.was_radix64 else "Ne"

        if result.was_signed:
            self.signature_label.text = "VALIDAN" if result.signature_valid else "NIJE validan"
            self.signer_label.text = f"{result.signer_name or '—'} <{result.signer_email or '—'}>"
        else:
            self.signature_label.text = "Poruka nije potpisana"
            self.signer_label.text = "—"

        text = result.plaintext.decode("utf-8", errors="replace") if result.plaintext else ""
        self.message_display.text = text
        self.last_plaintext = result.plaintext

    def _on_save_message(self):
        if not self.last_plaintext:
            show_message("Upozorenje", "Nema obrađene poruke za čuvanje.")
            return

        def _save(destination):
            try:
                with open(destination, "wb") as f:
                    f.write(self.last_plaintext)
            except Exception as e:
                show_message("Greška", f"Čuvanje nije uspelo:\n{e}")
                return
            show_message("Uspeh", f"Poruka je sačuvana u:\n{destination}")

        show_save_file_popup(on_selected=_save, title="Sačuvaj originalnu poruku kao...",
                              default_name="poruka.txt")
