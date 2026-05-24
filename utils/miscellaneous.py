from pywinauto.application import Application

import comtypes.client

comtypes.client._generate.gen_dir = None
import dearpygui.dearpygui as dpg
import os
import pyperclip
import requests
import subprocess
import winsound

from utils.config import Config
from utils.registry import reg_manager
from utils.statusbar import StatusBar


def check_model_path() -> None | str:
    StatusBar.clear_info()

    model_file = dpg.get_value("inp_model")
    if model_file == "":
        StatusBar.error_info("ERROR: Enter the model name.")
        return

    if not model_file.endswith(".m2"):
        if os.path.isdir(model_file):
            files = os.listdir(model_file)
            for file in files:
                if file.lower().endswith(".m2"):
                    model_file = os.path.join(model_file, file)
                    break

    if not "Export" in model_file and len(model_file) > len(os.path.basename(model_file)) + 1:
        model_name = os.path.basename(model_file)
        path = os.path.dirname(model_file)
        model_file = os.path.join(path + "\\Export\\", model_name)
    if not model_file.lower().endswith('.m2'):
        if model_file.lower().endswith("export") or model_file.lower().endswith("export\\"):
            if os.path.isdir(model_file):
                files = os.listdir(model_file)
                for file in files:
                    if file.lower().endswith(".m2"):
                        model_file = os.path.join(model_file, file)
                        break
        else:
            model_file += '.m2'

    wow_export_folder = reg_manager.wowExportFolder
    patch_folder = reg_manager.patchFolder
    separated_name = edit_model_name(model_file)
    model_type_path = get_model_type_path(separated_name)
    name_file = os.path.basename(model_file)

    # Сначала проверяем есть м2 в рабочей папке, потом в папке wow.export
    if os.path.exists(model_file):
        file_path = model_file
    elif os.path.exists(wow_export_folder + "\\" + model_type_path + "\\Export\\" + separated_name):
        file_path = wow_export_folder + "\\" + model_type_path + "\\Export\\" + separated_name
    elif os.path.exists(patch_folder + "\\" + model_type_path + "\\" + separated_name):
        file_path = patch_folder + "\\" + model_type_path + "\\" + separated_name
    elif os.path.exists(patch_folder + "\\" + model_type_path + "\\" + name_file):
        file_path = patch_folder + "\\" + model_type_path + "\\" + name_file
    else:
        StatusBar.error_info("ERROR: Enter valid name of m2 file.")
        return

    dpg.set_value("inp_model", file_path)
    return file_path


def download_listfile():
    listfile_folder = reg_manager.listfileFolder
    if listfile_folder == "":
        return

    github_url = "https://github.com/wowdev/wow-listfile/releases/latest/download/community-listfile.csv"
    local_path = listfile_folder + "\\community-listfile.csv"
    downloaded = 0

    if os.path.exists(local_path):
        local_listfile_size = os.path.getsize(local_path)
    else:
        local_listfile_size = 0

    try:
        response = requests.get(github_url, stream=True)
        response.raise_for_status()
        github_listfile_size = int(response.headers.get('Content-Length'))
        if github_listfile_size != local_listfile_size:
            with open(listfile_folder + "\\community-listfile.csv", 'wb') as csvfile:
                for chunk in response.iter_content(chunk_size=8192):
                    downloaded += len(chunk)
                    percent = int(downloaded / github_listfile_size * 100)
                    csvfile.write(chunk)
                    StatusBar.success_info("Downloading new listfile: " + str(percent) + " %")

            StatusBar.success_info("community-listfile.csv downloaded successfully.")

    except requests.exceptions.RequestException:
        StatusBar.error_info("ERROR: community-listfile.csv failed to download.")


def edit_model_name(model_file: str) -> None | str:
    if model_file is None:
        return

    separated_name = os.path.basename(model_file)
    return separated_name


def get_exported_model():
    try:
        wow_export_app = Application(backend="uia").connect(title_re="wow.export v*")
    except:
        StatusBar.error_info("ERROR: wow.export is not running.")
        return

    wow_export_window = wow_export_app[wow_export_app.windows()[0]]
    wow_export_status = wow_export_window.child_window(title_re=r"Successfully exported*", control_type="Text").window_text()
    if wow_export_status.startswith("Successfully exported "):
        if os.path.exists("C:\\Windows\\Media\\Speech Sleep.wav"):
            winsound.PlaySound("C:\\Windows\\Media\\Speech Sleep.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
        exported_model_path = os.path.join(reg_manager.wowExportFolder, wow_export_status[22:-1].replace("/", "\\"))
        pyperclip.copy(exported_model_path)

        StatusBar.success_info("Path copied to clipboard.")


def get_model_type_path(separated_name: str) -> None | str:
    if separated_name is None:
        StatusBar.error_info("ERROR: Enter correct m2 file name.")
        return

    all_checkboxes_status = [dpg.get_value(checkbox) for checkbox in Config.ALL_CHECKBOXES]
    if not any(all_checkboxes_status):
        StatusBar.error_info("ERROR: Select model type.")
        return
    else:
        StatusBar.clear_info()
        if dpg.get_value("chk_Creature"):
            model_type_path = f"creature\\{separated_name[:-3]}"
        elif dpg.get_value("chk_Spell"):
            model_type_path = "spells"
        elif dpg.get_value("chk_Skybox"):
            model_type_path = "environments\\stars"
        elif dpg.get_value("chk_Weapon"):
            model_type_path = "item\\objectcomponents\\weapon"
        elif dpg.get_value("chk_Shield"):
            model_type_path = "item\\objectcomponents\\shield"
        elif dpg.get_value("chk_Head"):
            model_type_path = "item\\objectcomponents\\head"
        elif dpg.get_value("chk_Shoulder"):
            model_type_path = "item\\objectcomponents\\shoulder"
        elif dpg.get_value("chk_Quiver"):
            model_type_path = "item\\objectcomponents\\quiver"
        elif dpg.get_value("chk_Ammo"):
            model_type_path = "item\\objectcomponents\\ammo"
        elif dpg.get_value("chk_Collections"):
            model_type_path = "item\\objectcomponents\\collections"
        elif dpg.get_value("chk_Doodads"):
            model_type_path = f"doodads\\{separated_name[:-3]}"

    return model_type_path


def open_file():
    file_path = check_model_path()
    if file_path is None:
        return

    subprocess.Popen(('start', "", file_path), shell=True)


def open_patch_folder():
    patch_folder = reg_manager.patchFolder
    if os.path.isdir(patch_folder):
        subprocess.Popen(['explorer', patch_folder])
    else:
        os.mkdir(patch_folder)
        subprocess.Popen(['explorer', patch_folder])


def open_skin():
    file_path = check_model_path()
    if file_path is None:
        return

    for i in range(4):
        skin_path = file_path[:-3] + '0' + str(i) + ".skin"
        if os.path.isfile(skin_path):
            subprocess.Popen(('start', "", skin_path), shell=True)


def open_wowexport_folder():
    subprocess.Popen(['explorer', reg_manager.wowExportFolder])


def run_wow():
    wow_folder = os.path.dirname(reg_manager.patchFolder)
    wow_path = wow_folder[:-9] + "wow.exe"
    if os.path.isfile(wow_path):
        subprocess.Popen(('start', "", wow_path), shell=True)
    else:
        StatusBar.error_info("ERROR: Wow.exe not found.")
