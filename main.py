"""
main.py

Ulazna tačka PGP aplikacije (Kivy GUI).

Pokretanje:
    pip install -r requirements.txt
    python main.py
"""

from gui.main_app import PGPApp


def main():
    PGPApp().run()


if __name__ == "__main__":
    main()
