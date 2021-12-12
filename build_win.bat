python -m pip install -r requirements.txt
python hours_builder.py
cd app
pyinstaller --onefile hours.py --exclude-module matplotlib --exclude-module qt5 --icon ../images/icon.ico
