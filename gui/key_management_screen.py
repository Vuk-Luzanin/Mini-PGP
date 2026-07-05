"""
gui/key_management_screen.py

Prikaz prstena javnih i privatnih ključeva (kao "tabele" realizovane
preko GridLayout + ScrollView), sa mogućnostima: generisanja novog
para, brisanja postojećeg, uvoza i izvoza ključeva.

Izmene u ovoj verziji:
- Klik na red sada jasno vizuelno označava selekciju (obojena pozadina,
  podebljan tekst, strelica na početku reda).
- Redovi imaju naizmenične ("zebra") pozadinske boje radi čitljivosti.
- Zaglavlje tabela i alatna traka su vizuelno doterani (boje, razmak,
  zaobljeni uglovi).
- Selekcija je "ekskluzivna" između dve tabele: kada izaberete red u
  jednoj tabeli, selekcija u drugoj se automatski poništava.
"""

from cryptography.hazmat.primitives import serialization
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, RoundedRectangle

from gui.key_generation_popup import KeyGenerationPopup
from gui.key_import_export_popup import ImportKeyPopup, ExportKeyPopup
from gui.message_popup import show_message, show_confirm


PUBLIC_COLUMNS = (
    ("ID ključa", 0.13, lambda entry: entry.key_id, False),
    ("Ime", 0.16, lambda entry: entry.user_name, False),
    ("E-mail", 0.22, lambda entry: entry.user_email, False),
    ("Veličina", 0.08, lambda entry: str(entry.key_size), False),
    ("Kreiran", 0.14, lambda entry: entry.created_at.strftime("%Y-%m-%d %H:%M"), False),
    ("Javni ključ", 0.27, lambda entry: _public_key_suffix(entry.public_key_pem), False),
)

PRIVATE_COLUMNS = (
    ("ID ključa", 0.11, lambda entry: entry.key_id, False),
    ("Ime", 0.14, lambda entry: entry.user_name, False),
    ("E-mail", 0.18, lambda entry: entry.user_email, False),
    ("Veličina", 0.07, lambda entry: str(entry.key_size), False),
    ("Kreiran", 0.13, lambda entry: entry.created_at.strftime("%Y-%m-%d %H:%M"), False),
    ("Javni ključ", 0.22, lambda entry: _public_key_suffix(entry.public_key_pem), False),
    (
        "Šifrovani privatni ključ",
        0.25,
        lambda entry: _blob_suffix(entry.encrypted_private_key_pem),
        False,
    ),
)


# ---------------------------------------------------------------------------
# Paleta boja
# ---------------------------------------------------------------------------
COLOR_HEADER_BG = (0.15, 0.19, 0.26, 1)
COLOR_HEADER_TEXT = (0.95, 0.96, 0.98, 1)

COLOR_ROW_EVEN = (0.97, 0.97, 0.99, 1)
COLOR_ROW_ODD = (0.91, 0.93, 0.96, 1)
COLOR_ROW_SELECTED = (0.20, 0.47, 0.85, 1)

COLOR_TEXT_NORMAL = (0.12, 0.13, 0.16, 1)
COLOR_TEXT_SELECTED = (1, 1, 1, 1)

COLOR_SECTION_BG = (0.20, 0.47, 0.85, 1)
COLOR_SECTION_TEXT = (1, 1, 1, 1)

COLOR_TOOLBAR_BTN = (0.20, 0.47, 0.85, 1)
COLOR_TOOLBAR_BTN_DANGER = (0.80, 0.28, 0.28, 1)


def _suffix_hex(data: bytes, bits: int = 128) -> str:
    if not data:
        return ""
    suffix = data[-(bits // 8):]
    return f"...{suffix.hex()}"


def _public_key_suffix(public_key_pem: bytes) -> str:
    if not public_key_pem:
        return ""
    public_key = serialization.load_pem_public_key(public_key_pem)
    modulus = public_key.public_numbers().n
    lower_128 = modulus & ((1 << 128) - 1)
    return f"...{lower_128:032x}"


def _blob_suffix(blob: bytes) -> str:
    return _suffix_hex(blob, bits=128)


class _ColoredBox(BoxLayout):
    """BoxLayout sa jednobojnom, po želji zaobljenom pozadinom."""

    def __init__(self, bg_color, radius=0, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self._color_instruction = Color(*bg_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        self.bind(pos=self._sync_rect, size=self._sync_rect)

    def _sync_rect(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def set_bg_color(self, bg_color):
        self._color_instruction.rgba = bg_color


class KeyRow(_ColoredBox):
    """Jedan red tabele koji jasno reaguje na klik/selekciju."""

    def __init__(self, key_id, columns, entry, row_height, on_select, base_color, **kwargs):
        super().__init__(
            bg_color=base_color,
            radius=6,
            orientation="horizontal",
            size_hint_y=None,
            height=row_height,
            spacing=4,
            padding=(8, 4),
            **kwargs,
        )
        self.key_id = key_id
        self.on_select = on_select
        self.base_color = base_color
        self.selected = False

        self._marker = Label(text="", size_hint_x=0.05, bold=True, color=COLOR_TEXT_SELECTED)
        self.add_widget(self._marker)

        self._labels = []
        for _, weight, accessor, _ in columns:
            value = accessor(entry)
            cell = Label(
                text=value,
                size_hint_x=weight,
                halign="left",
                valign="middle",
                color=COLOR_TEXT_NORMAL,
                shorten=True,
                shorten_from="right",
            )
            cell.bind(size=self._sync_label_text_size)
            self._labels.append(cell)
            self.add_widget(cell)

    @staticmethod
    def _sync_label_text_size(widget, *_):
        widget.text_size = widget.size

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.on_select(self.key_id)
            return True
        return super().on_touch_down(touch)

    def set_selected(self, selected):
        self.selected = selected
        if selected:
            self.set_bg_color(COLOR_ROW_SELECTED)
            self._marker.text = "\u25b6"  # ▶
            for lbl in self._labels:
                lbl.color = COLOR_TEXT_SELECTED
                lbl.bold = True
        else:
            self.set_bg_color(self.base_color)
            self._marker.text = ""
            for lbl in self._labels:
                lbl.color = COLOR_TEXT_NORMAL
                lbl.bold = False


class KeyTable(BoxLayout):
    """Jednostavna 'tabela' (lista redova) sa jasno vidljivom selekcijom reda."""

    def __init__(self, columns, group_name, row_height, on_selection_changed=None, **kwargs):
        super().__init__(orientation="vertical", spacing=4, **kwargs)
        self.columns = columns
        self.group_name = group_name
        self.row_height = row_height
        self.on_selection_changed = on_selection_changed
        self.selected_key_id = None
        self._rows = {}

        header = _ColoredBox(
            bg_color=COLOR_HEADER_BG,
            radius=6,
            size_hint_y=None,
            height=34,
            spacing=4,
            padding=(8, 0),
        )
        header.add_widget(Label(text="", size_hint_x=0.05))
        for text, weight, _, _ in self.columns:
            header.add_widget(
                Label(text=text, bold=True, size_hint_x=weight, color=COLOR_HEADER_TEXT)
            )
        self.add_widget(header)

        scroll = ScrollView(size_hint=(1, 1))
        self.rows_layout = GridLayout(cols=1, size_hint_y=None, spacing=3, padding=(0, 3))
        self.rows_layout.bind(minimum_height=self.rows_layout.setter("height"))
        scroll.add_widget(self.rows_layout)
        self.add_widget(scroll)

    def set_entries(self, entries):
        self.rows_layout.clear_widgets()
        self._rows = {}
        self.selected_key_id = None

        for index, entry in enumerate(entries):
            base_color = COLOR_ROW_EVEN if index % 2 == 0 else COLOR_ROW_ODD
            row = KeyRow(
                key_id=entry.key_id,
                columns=self.columns,
                entry=entry,
                row_height=self.row_height,
                on_select=self._select_row,
                base_color=base_color,
            )
            self._rows[entry.key_id] = row
            self.rows_layout.add_widget(row)

    def _select_row(self, key_id):
        if self.selected_key_id == key_id:
            # Ponovni klik na već izabrani red ga poništava.
            self._rows[key_id].set_selected(False)
            self.selected_key_id = None
        else:
            if self.selected_key_id is not None and self.selected_key_id in self._rows:
                self._rows[self.selected_key_id].set_selected(False)
            self._rows[key_id].set_selected(True)
            self.selected_key_id = key_id

        if self.on_selection_changed:
            self.on_selection_changed(self)

    def clear_selection(self):
        if self.selected_key_id is not None and self.selected_key_id in self._rows:
            self._rows[self.selected_key_id].set_selected(False)
        self.selected_key_id = None


class _SectionLabel(_ColoredBox):
    """Naslov sekcije sa obojenom trakom u pozadini."""

    def __init__(self, text, **kwargs):
        super().__init__(
            bg_color=COLOR_SECTION_BG,
            radius=6,
            size_hint_y=None,
            height=30,
            padding=(10, 0),
            **kwargs,
        )
        self.add_widget(Label(text=text, bold=True, color=COLOR_SECTION_TEXT, halign="left"))


class _StyledButton(Button):
    def __init__(self, text, bg_color=COLOR_TOOLBAR_BTN, **kwargs):
        super().__init__(
            text=text,
            background_normal="",
            background_down="",
            background_color=bg_color,
            color=(1, 1, 1, 1),
            bold=True,
            **kwargs,
        )


class KeyManagementScreen(BoxLayout):
    def __init__(self, key_manager, **kwargs):
        super().__init__(orientation="vertical", padding=10, spacing=10, **kwargs)
        self.key_manager = key_manager
        self.keyring = key_manager.keyring

        # ----- Toolbar -----
        toolbar = BoxLayout(size_hint_y=None, height=46, spacing=8)
        gen_btn = _StyledButton("Generiši par ključeva")
        gen_btn.bind(on_release=lambda *_: self._on_generate())
        import_btn = _StyledButton("Uvezi ključ")
        import_btn.bind(on_release=lambda *_: self._on_import())
        export_btn = _StyledButton("Izvezi izabrani")
        export_btn.bind(on_release=lambda *_: self._on_export())
        delete_btn = _StyledButton("Obriši izabrani", bg_color=COLOR_TOOLBAR_BTN_DANGER)
        delete_btn.bind(on_release=lambda *_: self._on_delete())
        refresh_btn = _StyledButton("Osveži", bg_color=(0.35, 0.38, 0.42, 1))
        refresh_btn.bind(on_release=lambda *_: self.refresh())

        for b in (gen_btn, import_btn, export_btn, delete_btn, refresh_btn):
            toolbar.add_widget(b)
        self.add_widget(toolbar)

        # ----- Public keys -----
        self.add_widget(_SectionLabel("Prsten javnih ključeva"))
        self.public_table = KeyTable(
            PUBLIC_COLUMNS,
            group_name="public_key_row",
            row_height=56,
            on_selection_changed=self._on_table_selection_changed,
            size_hint_y=0.42,
        )
        self.add_widget(self.public_table)

        # ----- Private keys -----
        self.add_widget(_SectionLabel("Prsten privatnih ključeva"))
        self.private_table = KeyTable(
            PRIVATE_COLUMNS,
            group_name="private_key_row",
            row_height=56,
            on_selection_changed=self._on_table_selection_changed,
            size_hint_y=0.42,
        )
        self.add_widget(self.private_table)

        info_label = Label(
            text="Napomena: svaki pristup privatnom ključu zahteva unos lozinke.",
            size_hint_y=None,
            height=24,
            color=(0.45, 0.45, 0.48, 1),
            italic=True,
        )
        self.add_widget(info_label)

        self.refresh()

    def refresh(self):
        self.public_table.set_entries(self.keyring.list_public_keys())
        self.private_table.set_entries(self.keyring.list_private_keys())

    def _on_table_selection_changed(self, table):
        # Selekcija je ekskluzivna: izbor u jednoj tabeli briše izbor u drugoj.
        if table is self.public_table:
            self.private_table.clear_selection()
        else:
            self.public_table.clear_selection()

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
            except Exception as e:
                show_message("Greška", f"Brisanje nije uspelo:\n{e}")
                return
            self.refresh()

        show_confirm("Potvrda", f"Obrisati par ključeva '{key_id}'?", on_yes=_confirmed)