# This script compiles .po files into .mo files for the specified languages.
# It uses the polib library to handle the .po files.
# Make sure to install polib with `pip install polib` if you haven't already.
#
import polib
import os

languages = ['ru', 'en', 'uk', 'pt']
base_dir = os.path.join(os.path.dirname(__file__), 'locales')

for lang in languages:
    po_path = os.path.join(base_dir, lang, 'bot.po')
    mo_path = os.path.join(base_dir, lang, 'bot.mo')
    if os.path.exists(po_path):
        po = polib.pofile(po_path)
        po.save_as_mofile(mo_path)
        print(f"Compiled {po_path} -> {mo_path}")
    else:
        print(f"Skipped missing file: {po_path}")
