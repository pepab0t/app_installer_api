import os

try:
    import requests
except ImportError:
    print('Missing requirement: requests. Please connect to wi-fi and execute command: "pip install requests==2.26.0"')
    os.system('pause')
    exit()


import re
import shutil
import warnings
from pathlib import Path

warnings.simplefilter("ignore")

PATH: Path = Path(__file__).parent.resolve()
URL: str = 'https://czrmpra-fp01:5000'
#URL: str = 'http://localhost:8000'
__fname__: str = re.split(r'/|\\', __file__)[-1]

def clear_dir():
    for item in os.listdir(PATH):
        if item == __fname__:
            continue

        if os.path.isdir(item):
            shutil.rmtree(item)
        else:
            os.remove(item)

def get_available_apps() -> list[str]:
    try:
        response = requests.get(f"{URL}/app/all", verify=False, timeout=2)
    except requests.exceptions.ConnectionError:
        raise Exception('Unable to connect to API, make sure you are connected to ZScaler or LAN network')
    
    return [k for k, v in response.json().items() if v['version'] is not None]

def get_app_source(app_name: str) -> str:
    try:
        response = requests.get(f'{URL}/app/download/{app_name}', verify=False, timeout=2)
    except requests.exceptions.ConnectionError:
        raise Exception('Unable to connect to API, make sure you are connected to ZScaler or LAN network')

    if not response.ok:
        raise Exception('Bad response from API')

    match = re.search(r'"(\w+.zip)"', response.headers['content-disposition'])
    if match is None:
        raise Exception('Invalid file returned from API')

    app_zipfile = match[1]

    with open(app_zipfile, 'wb') as f:
        f.write(response.content)

    return app_zipfile

def download_packages():
    done_char = "#"#"\u2588"
    undone_char = "-"
    response = requests.get("https://czrmpra-fp01:5000/libraries/download", verify=False, stream=True)

    if not response.ok:
        return

    total_length = int(response.headers.get('content-length'))  # type: ignore


    dl = 0
    with open('file.zip', 'wb') as f:
        for data in response.iter_content(chunk_size=4096):
            dl += len(data)

            done = (50 * dl/total_length)
            f.write(data)
            print(f"\r{(done/50 * 100):5.1f}% |{done_char*int(done)+undone_char*(50-int(done))}|", end='')

def main():
    try:
        _apps = get_available_apps()
    except Exception as e:
        print(e)
        os.system('pause')
        exit()

    if not _apps:
        print('Sorry, There are no available apps.')
        os.system('pause')
        return
    apps = {str(i): app for i, app in enumerate(_apps, start=1)}
    packs = {str(len(apps)): 'Download python packages'}
    while True:
        os.system('cls')
        print('Welcome to APP INSTALLER')
        print('New app will be installed to the folder, where this script is located.')
        print(PATH)
        print('Be careful! This process removes entire content of the directory.\n')
        print('Available apps:')
        for i, app in apps.items(): 
            print(f"{i} - {app}")
        print('-----------------\nE - exit installer\n')
        choice: str = input('>> ').upper()

        if choice.upper() == 'E':
            return

        if choice in apps:
            print('Installing ...')
            clear_dir()
            try:
                app_source = get_app_source(apps[choice])
            except Exception as e:
                print(e)
                return
            shutil.unpack_archive(app_source, PATH)
            os.remove(app_source)
            print('Sucessfully installed')
            print('Start app with file: main.py')
            os.system('pause')
            return

if __name__ == "__main__":
    main()



