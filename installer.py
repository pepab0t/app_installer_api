import os
import subprocess
from typing import Optional

try:
    import requests
except ImportError:
    print('Missing requirement: requests. Please connect to wi-fi and execute command: "pip install requests==2.26.0"')
    print("python requests installation required, please connect to Wi-Fi")
    os.system('pause')
    subprocess.run(["pip", "install", "requests==2.26.0"])
    try:
        import requests
    except ImportError:
        exit()

import re
import shutil
import sys
import warnings
from pathlib import Path

warnings.simplefilter("ignore")

PATH: Path = Path(__file__).parent.resolve()
URL: str = 'https://czrmpra-fp01:5000'
#URL: str = 'http://localhost:8000'
PACKAGE_ZIP: str = 'site-packages-temp.zip'
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
        response = requests.get(f"{URL}/app/all", verify=False)
    except requests.exceptions.ConnectionError:
        raise Exception('Unable to connect to API, make sure you are connected to ZScaler or LAN network')
    
    return [k for k, v in response.json().items() if v['version'] is not None]

def get_app_source(app_name: str) -> str:
    try:
        response = requests.get(f'{URL}/app/download/{app_name}', verify=False)
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

def download_packages() -> Optional[str]:
    done_char = "#"#"\u2588"
    undone_char = "-"
    try:
        response = requests.get("https://czrmpra-fp01:5000/libraries/download", verify=False, stream=True)
    except Exception:
        print("Unable to access server")
        return

    if not response.ok:
        print("Invalid response from server")
        return

    total_length = int(response.headers.get('content-length'))  # type: ignore

    dl = 0
    with open(PACKAGE_ZIP, 'wb') as f:
        for data in response.iter_content(chunk_size=4096):
            dl += len(data)

            done = (50 * dl/total_length)
            f.write(data)
            print(f"\r{(done/50 * 100):5.1f}% |{done_char*int(done)+undone_char*(50-int(done))}|", end='')

    print("\nDownloaded successfully!")
    return PACKAGE_ZIP

def get_lib_dir() -> Optional[Path]:
    interpreter_dir = Path(sys.executable).parent

    if 'Lib' in os.listdir(interpreter_dir):
        lib_dir = interpreter_dir / "Lib"
    else:
        lib_dir = interpreter_dir.parent / "Lib"

    if 'site-packages' in os.listdir(lib_dir):
        return lib_dir
    else:
        return None

def extract_packages(lib_dir, zip_name):
    print('Extracting downloaded packages.')

    for pkg in os.listdir(lib_dir / "site-packages"):
        try:
            shutil.rmtree(lib_dir / "site_packages" / pkg) 
        except Exception:
            continue
    shutil.unpack_archive(f'./{zip_name}', lib_dir)
    if os.path.exists(PACKAGE_ZIP):
        os.remove(PACKAGE_ZIP)


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
    packs = {str(len(apps)+1): 'Download python packages'}
    if len(sys.argv) == 1:
        while True:
            os.system('cls')
            print('Welcome to APP INSTALLER'.upper())
            print('.'.join(map(str, sys.version_info[:3])))
            print('New app will be installed to the folder, where this script is located.')
            print(PATH)
            print('Be careful!:\n + Installing removes entire content of the directory')
            print(' + Downloading packages overwrites all packages of current python interpreter\n')
            print('Available apps:')
            for i, app in apps.items(): 
                print(f"{i} - {app}")
            for i, pack in packs.items(): 
                print(f"{i} - {pack}")
            print('-----------------\nE - exit installer\n')

            choice: str = input('>> ').upper()

            if choice.upper() == 'E':
                return
            elif choice in apps:
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
            elif choice in packs:
                print('Downloading packages ... ')
                zip_name = download_packages()
                if not zip_name:
                    print('Download Failed!')
                    continue
                lib_dir: Optional[Path] = get_lib_dir()
                if not lib_dir:
                    print('Cannot find python Lib directory')
                    continue
                extract_packages(lib_dir, zip_name)
                print('Packages successfully extracted :)')
                os.system("pause")
        
    if len(sys.argv) == 3 and sys.argv[1] == '-o':
        option = sys.argv[2]

        if option == 'packages': 
            zip_name = download_packages()
            if not zip_name:
                sys.exit(1)
            lib_dir: Optional[Path] = get_lib_dir()
            if not lib_dir:
                sys.exit(1)
            extract_packages(lib_dir, zip_name)
        else:
            print('invalid option')
            sys.exit(1)

    else:
        print(f"Invalid arguments: {sys.argv}")
        sys.exit(1)


if __name__ == "__main__":
    main()
