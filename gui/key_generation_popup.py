"""
gui/key_generation_popup.py

Kivy popup za generisanje novog para RSA ključeva: unos imena, mejla,
veličine ključa i lozinke za čuvanje privatnog ključa.
"""

from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button

from gui.message_popup import show_message


class KeyGenerationPopup(Popup):
    def __init__(self, key_manager, on_success=None, **kwargs):
        super().__init__(
            title="Generisanje novog para ključeva",
            size_hint=(0.85, 0.7),
            **kwargs
        )
        self.key_manager = key_manager
        self.on_success = on_success

        root = BoxLayout(orientation="vertical", padding=12, spacing=8)

        form = GridLayout(cols=2, spacing=8, size_hint_y=None, row_default_height=40)
        form.bind(minimum_height=form.setter("height"))

        form.add_widget(Label(text="Ime i prezime:", size_hint_x=0.4))
        self.name_input = TextInput(multiline=False)
        form.add_widget(self.name_input)

        form.add_widget(Label(text="E-mail adresa:", size_hint_x=0.4))
        self.email_input = TextInput(multiline=False)
        form.add_widget(self.email_input)

        form.add_widget(Label(text="Veličina ključa:", size_hint_x=0.4))
        self.key_size_spinner = Spinner(text="2048", values=["1024", "2048"])
        form.add_widget(self.key_size_spinner)

        form.add_widget(Label(text="Lozinka:", size_hint_x=0.4))
        self.password_input = TextInput(multiline=False, password=True)
        form.add_widget(self.password_input)

        form.add_widget(Label(text="Ponovi lozinku:", size_hint_x=0.4))
        self.password_confirm_input = TextInput(multiline=False, password=True)
        form.add_widget(self.password_confirm_input)

        root.add_widget(form)

        btn_row = BoxLayout(size_hint_y=None, height=44, spacing=8)
        generate_btn = Button(text="Generiši")
        generate_btn.bind(on_release=lambda *_: self._on_generate())
        cancel_btn = Button(text="Otkaži")
        cancel_btn.bind(on_release=lambda *_: self.dismiss())
        btn_row.add_widget(generate_btn)
        btn_row.add_widget(cancel_btn)
        root.add_widget(btn_row)

        self.content = root

    def _on_generate(self):
        name = self.name_input.text.strip()
        email = self.email_input.text.strip()
        key_size = int(self.key_size_spinner.text)
        password = self.password_input.text
        password_confirm = self.password_confirm_input.text

        if not name or not email:
            show_message("Greška", "Ime i e-mail su obavezni.")
            return
        if not password:
            show_message("Greška", "Lozinka je obavezna.")
            return
        if password != password_confirm:
            show_message("Greška", "Lozinke se ne poklapaju.")
            return

        try:
            # TODO: implementirati u core/key_manager.py
            self.key_manager.generate_key_pair(name, email, key_size, password)
        except NotImplementedError:
            show_message(
                "Nije implementirano",
                "Generisanje ključeva još nije implementirano (core/key_manager.py)."
            )
            return
        except Exception as e:
            show_message("Greška", f"Generisanje ključa nije uspelo:\n{e}")
            return

        if self.on_success:
            self.on_success()
        self.dismiss()
