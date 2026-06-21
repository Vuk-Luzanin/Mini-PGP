"""
gui/file_chooser_popup.py

Pomoćni file-chooser popup (zamena za tkinter filedialog), za izbor
postojećeg fajla (uvoz/učitavanje) i unos imena/destinacije pri čuvanju.
"""

import os
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label


def show_open_file_popup(on_selected, title="Izaberite fajl", filters=None):
    """on_selected(path) se zove sa izabranom putanjom, ili se ne zove
    ako korisnik otkaže."""
    layout = BoxLayout(orientation="vertical", padding=8, spacing=8)
    chooser = FileChooserListView(path=os.path.expanduser("~"), filters=filters or [])
    layout.add_widget(chooser)

    btn_row = BoxLayout(size_hint_y=None, height=44, spacing=8)
    open_btn = Button(text="Otvori")
    cancel_btn = Button(text="Otkaži")
    btn_row.add_widget(open_btn)
    btn_row.add_widget(cancel_btn)
    layout.add_widget(btn_row)

    popup = Popup(title=title, content=layout, size_hint=(0.9, 0.9))

    def _on_open(*_):
        if chooser.selection:
            path = chooser.selection[0]
            popup.dismiss()
            on_selected(path)

    open_btn.bind(on_release=_on_open)
    cancel_btn.bind(on_release=lambda *_: popup.dismiss())
    popup.open()
    return popup


def show_save_file_popup(on_selected, title="Sačuvaj kao...", default_name="output.pgp"):
    """on_selected(path) se zove sa punom putanjom za čuvanje."""
    layout = BoxLayout(orientation="vertical", padding=8, spacing=8)
    chooser = FileChooserListView(path=os.path.expanduser("~"), dirselect=True)
    layout.add_widget(chooser)

    name_row = BoxLayout(size_hint_y=None, height=40, spacing=8)
    name_row.add_widget(Label(text="Naziv fajla:", size_hint_x=0.3))
    name_input = TextInput(text=default_name, multiline=False)
    name_row.add_widget(name_input)
    layout.add_widget(name_row)

    btn_row = BoxLayout(size_hint_y=None, height=44, spacing=8)
    save_btn = Button(text="Sačuvaj")
    cancel_btn = Button(text="Otkaži")
    btn_row.add_widget(save_btn)
    btn_row.add_widget(cancel_btn)
    layout.add_widget(btn_row)

    popup = Popup(title=title, content=layout, size_hint=(0.9, 0.9))

    def _on_save(*_):
        directory = chooser.path
        filename = name_input.text.strip()
        if not filename:
            return
        full_path = os.path.join(directory, filename)
        popup.dismiss()
        on_selected(full_path)

    save_btn.bind(on_release=_on_save)
    cancel_btn.bind(on_release=lambda *_: popup.dismiss())
    popup.open()
    return popup
