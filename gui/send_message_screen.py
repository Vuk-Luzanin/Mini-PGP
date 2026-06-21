"""
gui/send_message_screen.py

Ekran za slanje poruke: unos teksta poruke, izbor opcija (potpisivanje,
enkripcija, kompresija, radix-64), izbor ključeva i simetričnog
algoritma, te čuvanje rezultujuće datoteke na izabranu destinaciju.
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.checkbox import CheckBox
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button

from core.pgp_engine import SendOptions, SymmetricAlgorithm
from gui.message_popup import show_message, show_password_prompt
from gui.file_chooser_popup import show_save_file_popup


class LabeledCheckbox(BoxLayout):
    def __init__(self, text, **kwargs):
        super().__init__(size_hint_y=None, height=34, spacing=6, **kwargs)
        self.checkbox = CheckBox(size_hint_x=None, width=34)
        self.add_widget(self.checkbox)
        self.add_widget(Label(text=text, halign="left", valign="middle"))

    @property
    def active(self):
        return self.checkbox.active


class SendMessageScreen(BoxLayout):
    def __init__(self, key_manager, pgp_engine, **kwargs):
        super().__init__(orientation="vertical", padding=8, spacing=8, **kwargs)
        self.key_manager = key_manager
        self.pgp_engine = pgp_engine
        self.keyring = key_manager.keyring

        self.add_widget(Label(text="Tekst poruke:", bold=True, size_hint_y=None, height=24))
        self.message_input = TextInput(multiline=True, size_hint_y=0.4)
        self.add_widget(self.message_input)

        options_box = GridLayout(cols=2, size_hint_y=None, spacing=6)
        options_box.bind(minimum_height=options_box.setter("height"))

        # Potpisivanje
        self.sign_checkbox = LabeledCheckbox("Potpiši poruku (SHA-1)")
        self.sign_checkbox.checkbox.bind(active=lambda *_: self._toggle_sign())
        options_box.add_widget(self.sign_checkbox)
        self.sign_key_spinner = Spinner(text="Izaberi privatni ključ", values=[], disabled=True,
                                         size_hint_y=None, height=34)
        options_box.add_widget(self.sign_key_spinner)

        # Enkripcija
        self.encrypt_checkbox = LabeledCheckbox("Enkriptuj poruku")
        self.encrypt_checkbox.checkbox.bind(active=lambda *_: self._toggle_encrypt())
        options_box.add_widget(self.encrypt_checkbox)
        self.encrypt_key_spinner = Spinner(text="Izaberi javni ključ primaoca", values=[], disabled=True,
                                            size_hint_y=None, height=34)
        options_box.add_widget(self.encrypt_key_spinner)

        options_box.add_widget(Label(text="Simetrični algoritam:"))
        self.symmetric_spinner = Spinner(
            text="Izaberi algoritam",
            values=[a.value for a in SymmetricAlgorithm],
            disabled=True,
            size_hint_y=None, height=34
        )
        options_box.add_widget(self.symmetric_spinner)

        # Kompresija / radix-64
        self.compress_checkbox = LabeledCheckbox("Komprimuj poruku")
        options_box.add_widget(self.compress_checkbox)
        self.radix64_checkbox = LabeledCheckbox("Konvertuj u radix-64")
        options_box.add_widget(self.radix64_checkbox)

        self.add_widget(options_box)

        btn_row = BoxLayout(size_hint_y=None, height=44, spacing=8)
        refresh_btn = Button(text="Osveži liste ključeva")
        refresh_btn.bind(on_release=lambda *_: self.refresh_key_lists())
        send_btn = Button(text="Pošalji poruku")
        send_btn.bind(on_release=lambda *_: self._on_send())
        btn_row.add_widget(refresh_btn)
        btn_row.add_widget(send_btn)
        self.add_widget(btn_row)

        self.refresh_key_lists()

    def _toggle_sign(self):
        self.sign_key_spinner.disabled = not self.sign_checkbox.active

    def _toggle_encrypt(self):
        disabled = not self.encrypt_checkbox.active
        self.encrypt_key_spinner.disabled = disabled
        self.symmetric_spinner.disabled = disabled

    def refresh_key_lists(self):
        private_ids = [f"{k.key_id} ({k.user_name})" for k in self.keyring.private_keys]
        public_ids = [f"{k.key_id} ({k.user_name})" for k in self.keyring.public_keys]
        self.sign_key_spinner.values = private_ids
        self.encrypt_key_spinner.values = public_ids

    @staticmethod
    def _extract_key_id(spinner_value):
        if not spinner_value or "(" not in spinner_value:
            return None
        return spinner_value.split(" ")[0]

    def _on_send(self):
        message = self.message_input.text.strip()
        if not message:
            show_message("Upozorenje", "Unesite tekst poruke.")
            return

        sign = self.sign_checkbox.active
        encrypt = self.encrypt_checkbox.active

        sign_key_id = self._extract_key_id(self.sign_key_spinner.text) if sign else None
        if sign and not sign_key_id:
            show_message("Upozorenje", "Izaberite privatni ključ za potpis.")
            return

        encrypt_key_id = self._extract_key_id(self.encrypt_key_spinner.text) if encrypt else None
        if encrypt and not encrypt_key_id:
            show_message("Upozorenje", "Izaberite javni ključ primaoca.")
            return

        symmetric_alg = None
        if encrypt:
            alg_value = self.symmetric_spinner.text
            if alg_value not in [a.value for a in SymmetricAlgorithm]:
                show_message("Upozorenje", "Izaberite simetrični algoritam.")
                return
            symmetric_alg = SymmetricAlgorithm(alg_value)

        options = SendOptions(
            sign=sign,
            sign_private_key_id=sign_key_id,
            encrypt=encrypt,
            encrypt_public_key_id=encrypt_key_id,
            symmetric_algorithm=symmetric_alg,
            compress=self.compress_checkbox.active,
            radix64=self.radix64_checkbox.active,
        )

        if sign:
            show_password_prompt(
                "Unesite lozinku za privatni ključ (potpisivanje):",
                on_submit=lambda password: self._choose_destination(message, options, password)
            )
        else:
            self._choose_destination(message, options, None)

    def _choose_destination(self, message, options, sign_password):
        def _save(destination):
            try:
                self.pgp_engine.send_message(message, options, sign_password, destination)
            except NotImplementedError:
                show_message(
                    "Nije implementirano",
                    "Slanje poruke još nije implementirano (core/pgp_engine.py)."
                )
                return
            except Exception as e:
                show_message("Greška", f"Slanje poruke nije uspelo:\n{e}")
                return
            show_message("Uspeh", f"Poruka je sačuvana u:\n{destination}")

        show_save_file_popup(on_selected=_save, title="Sačuvaj poruku kao...", default_name="poruka.pgp")
