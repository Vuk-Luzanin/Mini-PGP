"""
gui/key_import_export_popup.py

Popup-ovi za uvoz i izvoz ključeva (javnog dela ili celog para) u
.pem formatu.
"""

from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton

from gui.message_popup import show_message
from gui.file_chooser_popup import show_open_file_popup, show_save_file_popup


class ImportKeyPopup(Popup):
    """Popup za uvoz javnog ključa ili celog para ključeva."""

    def __init__(self, key_manager, on_success=None, **kwargs):
        super().__init__(title="Uvoz ključa", size_hint=(0.85, 0.7), **kwargs)
        self.key_manager = key_manager
        self.on_success = on_success
        self.import_type = "public"

        root = BoxLayout(orientation="vertical", padding=12, spacing=10)

        type_row = BoxLayout(size_hint_y=None, height=42, spacing=8)
        self.public_btn = ToggleButton(text="Samo javni ključ", group="import_type", state="down")
        self.pair_btn = ToggleButton(text="Ceo par ključeva", group="import_type")
        self.public_btn.bind(on_release=lambda *_: self._set_type("public"))
        self.pair_btn.bind(on_release=lambda *_: self._set_type("pair"))
        type_row.add_widget(self.public_btn)
        type_row.add_widget(self.pair_btn)
        root.add_widget(type_row)

        path_row = BoxLayout(size_hint_y=None, height=42, spacing=8)
        path_row.add_widget(Label(text="Putanja:", size_hint_x=0.25))
        self.path_input = TextInput(multiline=False)
        path_row.add_widget(self.path_input)
        browse_btn = Button(text="...", size_hint_x=0.15)
        browse_btn.bind(on_release=lambda *_: self._browse())
        path_row.add_widget(browse_btn)
        root.add_widget(path_row)

        meta_row = GridLayout(cols=2, size_hint_y=None, row_default_height=42, spacing=8)
        meta_row.bind(minimum_height=meta_row.setter("height"))

        meta_row.add_widget(Label(text="Ime:", size_hint_x=0.25))
        self.name_input = TextInput(multiline=False)
        meta_row.add_widget(self.name_input)

        meta_row.add_widget(Label(text="E-mail:", size_hint_x=0.25))
        self.email_input = TextInput(multiline=False)
        meta_row.add_widget(self.email_input)

        root.add_widget(meta_row)

        pwd_row = BoxLayout(size_hint_y=None, height=42, spacing=8)
        pwd_row.add_widget(Label(text="Lozinka:", size_hint_x=0.25))
        self.password_input = TextInput(multiline=False, password=True, disabled=True)
        pwd_row.add_widget(self.password_input)
        root.add_widget(pwd_row)

        root.add_widget(BoxLayout())  # spacer

        btn_row = BoxLayout(size_hint_y=None, height=44, spacing=8)
        import_btn = Button(text="Uvezi")
        import_btn.bind(on_release=lambda *_: self._on_import())
        cancel_btn = Button(text="Otkaži")
        cancel_btn.bind(on_release=lambda *_: self.dismiss())
        btn_row.add_widget(import_btn)
        btn_row.add_widget(cancel_btn)
        root.add_widget(btn_row)

        self.content = root

    def _set_type(self, value):
        self.import_type = value
        self.password_input.disabled = value != "pair"

    def _browse(self):
        show_open_file_popup(
            on_selected=lambda path: setattr(self.path_input, "text", path),
            title="Izaberite .pem fajl",
            filters=["*.pem"],
        )

    def _on_import(self):
        path = self.path_input.text.strip()
        if not path:
            show_message("Greška", "Izaberite .pem fajl.")
            return

        try:
            if self.import_type == "public":
                self.key_manager.import_public_key(
                    path,
                    user_name=self.name_input.text.strip() or None,
                    user_email=self.email_input.text.strip() or None,
                )
            else:
                password = self.password_input.text
                self.key_manager.import_key_pair(
                    path,
                    password,
                    user_name=self.name_input.text.strip() or None,
                    user_email=self.email_input.text.strip() or None,
                )
        except Exception as e:
            show_message("Greška", f"Uvoz nije uspeo:\n{e}")
            return

        if self.on_success:
            self.on_success()
        self.dismiss()


class ExportKeyPopup(Popup):
    """Popup za izvoz javnog ključa ili celog para ključeva."""

    def __init__(self, key_manager, key_id, is_private_available=False, **kwargs):
        super().__init__(title=f"Izvoz ključa — {key_id}", size_hint=(0.85, 0.7), **kwargs)
        self.key_manager = key_manager
        self.key_id = key_id
        self.export_type = "public"

        root = BoxLayout(orientation="vertical", padding=12, spacing=10)

        type_row = BoxLayout(size_hint_y=None, height=42, spacing=8)
        self.public_btn = ToggleButton(text="Samo javni ključ", group="export_type", state="down")
        self.pair_btn = ToggleButton(
            text="Ceo par ključeva", group="export_type",
            disabled=not is_private_available
        )
        self.public_btn.bind(on_release=lambda *_: self._set_type("public"))
        self.pair_btn.bind(on_release=lambda *_: self._set_type("pair"))
        type_row.add_widget(self.public_btn)
        type_row.add_widget(self.pair_btn)
        root.add_widget(type_row)

        pwd_row = BoxLayout(size_hint_y=None, height=42, spacing=8)
        pwd_row.add_widget(Label(text="Lozinka:", size_hint_x=0.25))
        self.password_input = TextInput(multiline=False, password=True, disabled=True)
        pwd_row.add_widget(self.password_input)
        root.add_widget(pwd_row)

        root.add_widget(BoxLayout())  # spacer

        btn_row = BoxLayout(size_hint_y=None, height=44, spacing=8)
        export_btn = Button(text="Izvezi")
        export_btn.bind(on_release=lambda *_: self._on_export())
        cancel_btn = Button(text="Otkaži")
        cancel_btn.bind(on_release=lambda *_: self.dismiss())
        btn_row.add_widget(export_btn)
        btn_row.add_widget(cancel_btn)
        root.add_widget(btn_row)

        self.content = root

    def _set_type(self, value):
        self.export_type = value
        self.password_input.disabled = value != "pair"

    def _on_export(self):
        default_name = f"{self.key_id}.pem"

        def _save(destination):
            try:
                if self.export_type == "public":
                    self.key_manager.export_public_key(self.key_id, destination)
                else:
                    password = self.password_input.text
                    self.key_manager.export_key_pair(self.key_id, password, destination)
            except Exception as e:
                show_message("Greška", f"Izvoz nije uspeo:\n{e}")
                return
            show_message("Uspeh", "Ključ je izvezen.")
            self.dismiss()

        show_save_file_popup(on_selected=_save, title="Izvezi ključ kao...", default_name=default_name)
