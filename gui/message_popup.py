"""
gui/message_popup.py

Pomoćna funkcija za prikaz jednostavnih informativnih/error popup
prozora (zamena za tkinter messagebox).
"""

from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button


def show_message(title: str, text: str, on_dismiss=None):
    layout = BoxLayout(orientation="vertical", padding=12, spacing=10)
    layout.add_widget(Label(text=text, halign="center", valign="middle"))

    btn = Button(text="OK", size_hint_y=None, height=42)
    layout.add_widget(btn)

    popup = Popup(title=title, content=layout, size_hint=(0.75, 0.4))
    btn.bind(on_release=lambda *_: popup.dismiss())
    if on_dismiss:
        popup.bind(on_dismiss=lambda *_: on_dismiss())
    popup.open()
    return popup


def show_confirm(title: str, text: str, on_yes=None):
    layout = BoxLayout(orientation="vertical", padding=12, spacing=10)
    layout.add_widget(Label(text=text, halign="center", valign="middle"))

    btn_row = BoxLayout(size_hint_y=None, height=42, spacing=8)
    yes_btn = Button(text="Da")
    no_btn = Button(text="Ne")
    btn_row.add_widget(yes_btn)
    btn_row.add_widget(no_btn)
    layout.add_widget(btn_row)

    popup = Popup(title=title, content=layout, size_hint=(0.75, 0.4))

    def _on_yes(*_):
        popup.dismiss()
        if on_yes:
            on_yes()

    yes_btn.bind(on_release=_on_yes)
    no_btn.bind(on_release=lambda *_: popup.dismiss())
    popup.open()
    return popup


def show_password_prompt(title: str, on_submit):
    """
    Prikazuje popup sa jednim poljem za unos lozinke i dugmićima
    Potvrdi/Otkaži. `on_submit(password)` se zove ako korisnik potvrdi
    (password može biti i prazan string).
    """
    from kivy.uix.textinput import TextInput

    layout = BoxLayout(orientation="vertical", padding=12, spacing=10)
    layout.add_widget(Label(text=title))
    password_input = TextInput(multiline=False, password=True, size_hint_y=None, height=40)
    layout.add_widget(password_input)

    btn_row = BoxLayout(size_hint_y=None, height=42, spacing=8)
    ok_btn = Button(text="Potvrdi")
    cancel_btn = Button(text="Otkaži")
    btn_row.add_widget(ok_btn)
    btn_row.add_widget(cancel_btn)
    layout.add_widget(btn_row)

    popup = Popup(title="Lozinka", content=layout, size_hint=(0.75, 0.4))

    def _on_ok(*_):
        password = password_input.text
        popup.dismiss()
        on_submit(password)

    ok_btn.bind(on_release=_on_ok)
    cancel_btn.bind(on_release=lambda *_: popup.dismiss())
    popup.open()
    return popup
