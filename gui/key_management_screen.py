"""
gui/key_management_screen.py

Prikaz prstena javnih i privatnih ključeva (kao "tabele" realizovane
preko GridLayout + ScrollView), sa mogućnostima: generisanja novog
para, brisanja postojećeg, uvoza i izvoza ključeva.
"""

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton

from gui.key_generation_popup import KeyGenerationPopup
from gui.key_import_export_popup import ImportKeyPopup, ExportKeyPopup
from gui.message_popup import show_message, show_confirm


HEADER_COLS = ("ID ključa", "Ime", "E-mail", "Veličina", "Kreiran")


class KeyTable(BoxLayout):
    """Jednostavna 'tabela' (lista redova) sa mogućnošću selekcije reda."""

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.selected_key_id = None
        self._row_buttons = {}

        header = GridLayout(cols=len(HEADER_COLS), size_hint_y=None, height=32)
        for text in HEADER_COLS:
            header.add_widget(Label(text=text, bold=True, size_hint_y=None, height=32))
        self.add_widget(header)

        scroll = ScrollView(size_hint=(1, 1))
        self.rows_layout = GridLayout(cols=1, size_hint_y=None, spacing=2)
        self.rows_layout.bind(minimum_height=self.rows_layout.setter("height"))
        scroll.add_widget(self.rows_layout)
        self.add_widget(scroll)

    def set_entries(self, entries):
        self.rows_layout.clear_widgets()
        self._row_buttons = {}
        self.selected_key_id = None

        for entry in entries:
            row_btn = ToggleButton(
                text=(
                    f"{entry.key_id:<12} {entry.user_name:<18} "
                    f"{entry.user_email:<22} {entry.key_size:<6} "
                    f"{entry.created_at.strftime('%Y-%m-%d %H:%M')}"
                ),
                size_hint_y=None,
                height=34,
                group="key_row",
                halign="left",
                valign="middle",
            )
            row_btn.bind(
                on_release=lambda btn, key_id=entry.key_id: self._on_row_selected(key_id)
            )
            self._row_buttons[entry.key_id] = row_btn
            self.rows_layout.add_widget(row_btn)

    def _on_row_selected(self, key_id):
        self.selected_key_id = key_id


class KeyManagementScreen(BoxLayout):
    def __init__(self, key_manager, **kwargs):
        super().__init__(orientation="vertical", padding=8, spacing=8, **kwargs)
        self.key_manager = key_manager
        self.keyring = key_manager.keyring

        # ----- Toolbar -----
        toolbar = BoxLayout(size_hint_y=None, height=44, spacing=6)
        gen_btn = Button(text="Generiši par ključeva")
        gen_btn.bind(on_release=lambda *_: self._on_generate())
        import_btn = Button(text="Uvezi ključ")
        import_btn.bind(on_release=lambda *_: self._on_import())
        export_btn = Button(text="Izvezi izabrani")
        export_btn.bind(on_release=lambda *_: self._on_export())
        delete_btn = Button(text="Obriši izabrani")
        delete_btn.bind(on_release=lambda *_: self._on_delete())
        refresh_btn = Button(text="Osveži")
        refresh_btn.bind(on_release=lambda *_: self.refresh())

        for b in (gen_btn, import_btn, export_btn, delete_btn, refresh_btn):
            toolbar.add_widget(b)
        self.add_widget(toolbar)

        # ----- Public keys -----
        self.add_widget(Label(text="Prsten javnih ključeva", bold=True, size_hint_y=None, height=26))
        self.public_table = KeyTable(size_hint_y=0.4)
        self.add_widget(self.public_table)

        # ----- Private keys -----
        self.add_widget(Label(text="Prsten privatnih ključeva", bold=True, size_hint_y=None, height=26))
        self.private_table = KeyTable(size_hint_y=0.4)
        self.add_widget(self.private_table)

        info_label = Label(
            text="Napomena: svaki pristup privatnom ključu zahteva unos lozinke.",
            size_hint_y=None,
            height=24,
            color=(0.4, 0.4, 0.4, 1),
        )
        self.add_widget(info_label)

        self.refresh()

    def refresh(self):
        self.public_table.set_entries(self.keyring.public_keys)
        self.private_table.set_entries(self.keyring.private_keys)

    def _selected_key_id(self):
        return self.public_table.selected_key_id or self.private_table.selected_key_id

    def _on_generate(self):
        KeyGenerationPopup(self.key_manager, on_success=self.refresh).open()

    def _on_import(self):
        ImportKeyPopup(self.key_manager, on_success=self.refresh).open()

    def _on_export(self):
        key_id = self._selected_key_id()
        if not key_id:
            show_message("Upozorenje", "Izaberite ključ iz tabele.")
            return
        is_private_available = self.keyring.find_private_key(key_id) is not None
        ExportKeyPopup(self.key_manager, key_id, is_private_available).open()

    def _on_delete(self):
        key_id = self._selected_key_id()
        if not key_id:
            show_message("Upozorenje", "Izaberite par ključeva za brisanje.")
            return

        def _confirmed():
            try:
                self.key_manager.delete_key_pair(key_id)
            except NotImplementedError:
                show_message(
                    "Nije implementirano",
                    "Brisanje ključeva još nije implementirano (core/key_manager.py)."
                )
                return
            except Exception as e:
                show_message("Greška", f"Brisanje nije uspelo:\n{e}")
                return
            self.refresh()

        show_confirm("Potvrda", f"Obrisati par ključeva '{key_id}'?", on_yes=_confirmed)
