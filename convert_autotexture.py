import dearpygui.dearpygui as dpg
import glob
import json
import os
import pyautogui
import pyperclip
import re
import shutil
import subprocess

from position_scale import auto_fix_helm_offset

from utils.binary import Binary
from utils.config import Config
from utils.miscellaneous import check_model_path, edit_model_name, get_model_type_path
from utils.offsets import M2Offsets, M2Lengths
from utils.registry import reg_manager
from utils.statusbar import StatusBar

RACES_PREFIXES = ("_be_f", "_be_m", "_bef", "_bem",
                  "_dr_f", "_dr_m", "_drf", "_drm",
                  "_dw_f", "_dw_m", "_dwf", "_dwm",
                  "_gn_f", "_gn_m", "_gnf", "_gnm",
                  "_hu_f", "_hu_m", "_huf", "_hum",
                  "_ni_f", "_ni_m", "_nif", "_nim",
                  "_or_f", "_or_m", "_orf", "_orm",
                  "_sc_f", "_sc_m", "_scf", "_scm",
                  "_ta_f", "_ta_m", "_taf", "_tam",
                  "_tr_f", "_tr_m", "_trf", "_trm",)

SPELLS_PREFIXES = ("_aura01", "_aura02", "_aura",
                   "cfx_", "fx_",
                   "_channel",
                   "_cast", "_cast01", "_cast02", "_precast", "_precast01", "_precast02",
                   "_impact", "_impact01", "_impact02",
                   "_missile01", "_missile",)


def auto_texture_pre():
    StatusBar.clear_info()

    file_path = check_model_path()
    separated_name = edit_model_name(file_path)
    model_type_path = get_model_type_path(separated_name)
    if file_path is None:
        StatusBar.error_info("ERROR: Enter correct m2 file name.")
        return

    auto_texture(separated_name, model_type_path, file_path)


def auto_texture(separated_name: str, model_type_path: str, file_path: str):
    BYTES_INDEXES = (0, 8, 12)
    all_textures = []
    all_textures_lengths = []
    all_textures_offsets = []
    work_folder = os.getcwd() + "\\"
    manifest_file = file_path[:-3] + ".manifest.json"
    separated_manifest_file = separated_name[:-3] + ".manifest.json"
    wow_export_folder = reg_manager.wowExportFolder

    # Если модель уже сконвертирована выходим
    if not is_converted(file_path):
        return

    # Сначала проверяем есть manifest в рабочей папке, потом в папках wow.export
    if os.path.isfile(manifest_file):
        manifest_path = manifest_file
    elif os.path.isfile(variant1 := manifest_file.replace("Export\\", "")):
        manifest_path = variant1
    elif os.path.isfile(variant2 := wow_export_folder + "\\" + model_type_path + "\\" + separated_manifest_file):
        manifest_path = variant2
    elif os.path.isfile(variant3 := wow_export_folder + "\\models\\" + model_type_path + "\\" + separated_manifest_file):
        manifest_path = variant3
    else:
        StatusBar.error_info("ERROR: Manifest file not found.")
        return

    # Сохраняем GlobalSeq
    if reg_manager.autoFixGlobalSeq:
        GlobalSeq_bytes = get_global_sequences(file_path)

    # Определяем число nViews и если нужно перезаписываем nViews в модель
    nViews = get_nViews(file_path)
    overwrite_nVies(file_path, nViews)

    # Конвертируем м2
    StatusBar.success_info("Converting model...")
    rename_lod(file_path, nViews)

    # Запускаем Multiconverter_Console
    subprocess.run(work_folder + "MultiConverter_Console.exe " + file_path, creationflags=subprocess.CREATE_NO_WINDOW,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Удаляем лог конвертера
    if os.path.isfile(work_folder + "error.log"):
        os.unlink(work_folder + "error.log")

    # Фиксим GlobalSeq
    if reg_manager.autoFixGlobalSeq:
        overwrite_global_sequences(file_path, GlobalSeq_bytes)

    # Прописываем текстуры
    with open(manifest_path) as manifest:
        manifest_json = json.load(manifest)

    for texture in manifest_json["textures"]:
        corrected_texture = correct_texture_path_from_manifest(texture['file'], file_path, wow_export_folder)
        all_textures.append(corrected_texture)

    # Прописываем полученные текстуры в модель
    with open(file_path, "ab") as m2_file:
        Binary.write_zeros(m2_file)

        for i, texture in enumerate(all_textures):
            if Config.pathPrefix == "environments\\stars\\":
                texture_full_path = Config.pathPrefix + all_textures[i]
            elif Config.pathPrefix == "creature\\" or Config.pathPrefix == "doodads\\":
                texture_full_path = Config.pathPrefix + separated_name[:-3] + "\\" + all_textures[i]
            else:
                texture_full_path = Config.pathPrefix + all_textures[i]
                if os.path.exists(wow_export_folder + "\\" + texture_full_path):
                    if os.path.exists(os.path.dirname(file_path) + "\\" + all_textures[i]):
                        os.remove(os.path.dirname(file_path) + "\\" + all_textures[i])
                    shutil.move(wow_export_folder + "\\" + texture_full_path, os.path.dirname(file_path))

            texture_full_path_bytes = texture_full_path.encode('utf-8')
            deficient_bytes_for_texture = 16 - len(texture_full_path_bytes) % 16
            all_textures_lengths.append(len(texture_full_path_bytes))

            if deficient_bytes_for_texture == 0:
                deficient_bytes_for_texture = 16

            texture_offset = m2_file.seek(0, 2)
            all_textures_offsets.append(texture_offset)
            m2_file.write(texture_full_path_bytes)
            m2_file.write(b'\00' * deficient_bytes_for_texture)

    with open(file_path, "rb+") as m2_file:
        textures_adress_start = Binary.get_int_from_bytes(m2_file, M2Offsets.ofsTextures)
        for i, texture in enumerate(all_textures):
            for i2, _ in enumerate(BYTES_INDEXES):
                m2_file.seek(textures_adress_start + M2Lengths.texture * i + BYTES_INDEXES[i2])
                if i2 == 0:
                    m2_file.write(b'\00')
                elif i2 == 1:
                    m2_file.write(all_textures_lengths[i].to_bytes(4, 'little'))
                elif i2 == 2:
                    m2_file.write(all_textures_offsets[i].to_bytes(4, 'little'))

        Binary.write_bytes(m2_file, M2Offsets.nTextures, len(all_textures).to_bytes(2, 'little'))

    # Удаляем ненужные лодсы и перемещаем все нужные файлы в папку Export
    remove_lod(file_path)
    move_textures_and_anims(file_path, model_type_path)

    # Переименовываем расовые предметы
    renamed_file_path = rename_race_items(model_type_path, file_path)
    dpg.set_value("inp_model", renamed_file_path)

    # Создаем текст для удобного copy/paste
    generate_model_name_text(model_type_path, renamed_file_path)

    # Выполняем Auto fix helm offset если стоит чекбокс
    if reg_manager.autoFixHelmOffset and model_type_path == r"item\objectcomponents\head":
        auto_fix_helm_offset(renamed_file_path)

    if not reg_manager.autoMoveFilesToPatch:
        dpg.configure_item("gr_move_files_to_path_folder", enabled=True)
    else:
        move_files_to_patch_pre()
        dpg.configure_item("gr_move_files_to_path_folder", enabled=False)

    # Перемещаем иконку в патч
    move_icon_to_patch(wow_export_folder, reg_manager.patchFolder)

    # Удаляем экспортированные данные
    if reg_manager.autoDeleteExportedData:
        remove_exported_data(file_path)

    StatusBar.success_info(f"{separated_name} converted with {nViews} skin(s) and {len(all_textures)} texture(s).")


def check_auto_move_files_to_patch():
    if reg_manager.autoMoveFilesToPatch:
        dpg.configure_item("gr_move_files_to_path_folder", enabled=False)
        dpg.configure_item("btn_move", label="AUTO MOVE TO PATCH 'ENABLED'")
    else:
        dpg.configure_item("gr_move_files_to_path_folder", enabled=False)
        dpg.configure_item("btn_move", label="MOVE FILES TO PATCH FOLDER")


def correct_texture_path_from_manifest(texture: str, file_path: str, wow_export_folder: str) -> str:
    folder_to = os.path.dirname(file_path) + "\\"
    corrected_texture_path = texture.replace("..\\", "")
    corrected_texture = os.path.basename(corrected_texture_path)
    OTHER_FOLDERS = ("\\world\\",
                     "\\world\\expansion09\\",
                     "\\world\\expansion10\\",
                     "\\world\\expansion09\\doodads\\",
                     "\\world\\expansion10\\doodads\\",
                     )

    # Перемешаем недостающие текстуры в папку с моделью
    source = os.path.join(wow_export_folder, corrected_texture_path)
    destination = os.path.join(folder_to, corrected_texture)
    if os.path.exists(source):
        shutil.move(source, destination)

    # проверяем может текстура есть в других папках
    for folder in OTHER_FOLDERS:
        if os.path.exists(os.path.join(wow_export_folder + folder, corrected_texture)):
            shutil.move(os.path.join(wow_export_folder + folder, corrected_texture), destination)

    return corrected_texture


def delete_last_moved_files():
    last_moved_files = delete_last_moved_files.lastMovedFiles
    try:
        if last_moved_files:
            if last_moved_files[0][len(reg_manager.patchFolder) + 1:].lower().startswith("creature"):
                shutil.rmtree(os.path.dirname(last_moved_files[0]))
            else:
                for file in last_moved_files:
                    os.remove(file)

            dpg.configure_item("gr_del_last_files", enabled=False)
            StatusBar.success_info(f"{len(last_moved_files)} files deleted.")
            last_moved_files.clear()
    except PermissionError:
        StatusBar.error_info("ERROR: Unable to delete. Files are using by another application.")


def generate_icon_name_text(model_type_path, name_file):
    file_name = name_file.replace(".m2", "")
    match model_type_path:
        case r"item\objectcomponents\weapon" | r"item\objectcomponents\shield" | r"item\objectcomponents\ammo" | \
             r"item\objectcomponents\quiver" | r"item\objectcomponents\collections":
            icon_name_for_copy = "inv_" + str(file_name)
        case r"item\objectcomponents\head":
            for race_prefix in RACES_PREFIXES:
                file_name = file_name.replace(race_prefix, "")
            model_name = file_name
            icon_name_for_copy = "inv_" + str(model_name)
        case r"item\objectcomponents\shoulder":
            if file_name.endswith("_l") or file_name.endswith("_r"):
                model_name = file_name[:-2]
            icon_name_for_copy = "inv_" + str(model_name)
        case r"environments\stars":
            icon_name_for_copy = ""
        case "spells":
            for spell_prefix in SPELLS_PREFIXES:
                file_name = file_name.replace(spell_prefix, "")
            model_name = file_name
            icon_name_for_copy = "ability_" + str(model_name)
        case _:
            icon_name_for_copy = "inv_" + str(file_name)

    dpg.set_value("inp_icon_name_for_copy", icon_name_for_copy)

    if icon_name_for_copy:
        dpg.configure_item("inp_icon_name_for_copy", width=len(icon_name_for_copy) * 7.4,
                           pos=[(Config.WINDOW_WIDTH - len(icon_name_for_copy) * 7.4) / 2.2, 180])
        dpg.configure_item("txt_left_arrows2", color=[255, 255, 255],
                           pos=[(Config.WINDOW_WIDTH - len(icon_name_for_copy) * 7.4) / 2.2 - 25, 180])
        dpg.configure_item("txt_right_arrows2", color=[255, 255, 255],
                           pos=[dpg.get_item_pos("inp_icon_name_for_copy")[0] + dpg.get_item_width("inp_icon_name_for_copy") + 4, 180])

        pyperclip.copy(icon_name_for_copy)

        StatusBar.copied_info("Icon name")
    else:
        dpg.configure_item("inp_icon_name_for_copy", width=280, pos=[193, 180])
        dpg.configure_item("txt_left_arrows2", color=[255, 255, 255], pos=[165, 180])
        dpg.configure_item("txt_right_arrows2", color=[255, 255, 255],
                           pos=[dpg.get_item_pos("inp_icon_name_for_copy")[0] + dpg.get_item_width("inp_icon_name_for_copy") + 4, 180])

    dpg.focus_item("inp_model")
    pyautogui.press("end")


def generate_model_name_text(model_type_path: str, file_path: str):
    file_name = os.path.basename(file_path).replace(".m2", ".mdx")
    match model_type_path:
        case r"item\objectcomponents\weapon" | r"item\objectcomponents\shield" | r"item\objectcomponents\ammo" | \
             r"item\objectcomponents\shoulder" | r"item\objectcomponents\quiver" | r"item\objectcomponents\collections":
            model_path_for_copy = file_name
        case r"item\objectcomponents\head":
            for race_prefix in RACES_PREFIXES:
                file_name = file_name.replace(race_prefix, "")
            model_path_for_copy = file_name
        case r"environments\stars":
            model_path_for_copy = os.path.join(str(model_type_path), str(file_name))
        case "spells":
            model_path_for_copy = os.path.join(str(model_type_path), str(file_name))
        case _:
            model_path_for_copy = os.path.join(str(model_type_path), str(file_name))

    dpg.set_value("inp_model_name_for_copy", model_path_for_copy)

    pyperclip.copy(model_path_for_copy)

    dpg.configure_item("inp_model_name_for_copy", width=len(model_path_for_copy) * 7.2,
                       pos=[(Config.WINDOW_WIDTH - len(model_path_for_copy) * 7.2) / 2.2, Config.WINDOW_HEIGHT - 820])
    dpg.configure_item("txt_left_arrows",
                       pos=[(Config.WINDOW_WIDTH - len(model_path_for_copy) * 7.2) / 2.2 - 25, Config.WINDOW_HEIGHT - 820])
    dpg.configure_item("txt_right_arrows",
                       pos=[dpg.get_item_pos("inp_model_name_for_copy")[0] + dpg.get_item_width("inp_model_name_for_copy") + 3,
                            Config.WINDOW_HEIGHT - 820])


def get_nViews(file_path: str) -> int:
    skin_file = file_path[:-3] + "00.skin"
    with open(skin_file, "rb") as skin_file:
        ofsSubmeshes = Binary.get_int_from_bytes(skin_file, 32)
        nBones = Binary.get_int_from_bytes(skin_file, ofsSubmeshes + 12, length=2)

        if nBones > 64:
            nViews = 4
        elif nBones > 53:
            nViews = 3
        elif nBones > 21:
            nViews = 2
        else:
            nViews = 1

    return nViews


def get_icon_name():
    StatusBar.clear_info()

    model_path = dpg.get_value("inp_model")
    if model_path.startswith('"') or model_path.endswith('"'):
        model_path = model_path.replace('"', '')
        if not model_path.endswith(".m2"):
            files = os.listdir(model_path)
            for file in files:
                if file.lower().endswith(".m2"):
                    model_path = os.path.join(model_path, file)
                    break

    if not "Export" in model_path and len(model_path) > len(os.path.basename(model_path)) + 1:
        model_name = os.path.basename(model_path)
        path = os.path.dirname(model_path)
        model_path = os.path.join(path + "\\Export\\", model_name)

    if not model_path.lower().endswith('.m2'):
        if model_path.lower().endswith("export") or model_path.lower().endswith("export\\"):
            files = os.listdir(model_path)
            for file in files:
                if file.lower().endswith(".m2"):
                    model_path = os.path.join(model_path, file)
                    break
        else:
            model_path += '.m2'

    wow_export_folder = reg_manager.wowExportFolder
    patch_folder = reg_manager.patchFolder
    separated_name = edit_model_name(model_path)
    model_type_path = get_model_type_path(separated_name)
    if model_type_path is None:
        return

    name_file = os.path.basename(model_path)

    # Сначала проверяем есть ли м2 в рабочей папке, потом в папке wow.export
    if os.path.exists(model_path):
        file_path = model_path
    elif os.path.exists(wow_export_folder + "\\" + model_type_path + "\\Export\\" + separated_name):
        file_path = wow_export_folder + "\\" + model_type_path + "\\Export\\" + separated_name
    elif os.path.exists(patch_folder + "\\" + model_type_path + "\\" + separated_name):
        file_path = patch_folder + "\\" + model_type_path + "\\" + separated_name
    elif os.path.exists(patch_folder + "\\" + model_type_path + "\\" + name_file):
        file_path = patch_folder + "\\" + model_type_path + "\\" + name_file
    else:
        StatusBar.error_info("ERROR: Enter valid path to m2 file.")
        return

    dpg.set_value("inp_model", file_path)
    generate_icon_name_text(model_type_path, name_file)


def get_global_sequences(file_path: str) -> bytes:
    file_path = file_path.replace("Export\\", "")
    with open(file_path, "rb+") as file_m2:
        nGlobalSeq = Binary.get_int_from_bytes(file_m2, 28)
        ofsGlobalSeq = Binary.get_int_from_bytes(file_m2, 32)
        GlobalSeq_bytes = Binary.read_bytes(file_m2, ofsGlobalSeq + 8, nGlobalSeq * 4)

    return GlobalSeq_bytes


def is_converted(file_path: str) -> bool:
    with open(file_path, "rb") as file_m2:
        md_structure = file_m2.read(4)
        if md_structure == b'\x4D\x44\x32\x30':
            StatusBar.error_info(f"{os.path.basename(file_path)} has already been converted.")
            return False
        else:
            return True


def move_files_to_patch_pre():
    file_path = check_model_path()
    separated_name = edit_model_name(file_path)
    model_type_path = get_model_type_path(separated_name)

    move_files_to_patch(file_path, reg_manager.patchFolder, model_type_path)


def move_files_to_patch(file_path: str, patch_folder: str, model_type_path: str):
    delete_last_moved_files.lastMovedFiles.clear()
    try:
        folder_from = os.path.dirname(file_path) + "\\"
    except TypeError:
        StatusBar.error_info("ERROR: There are no files to move.")
        dpg.configure_item("gr_move_files_to_path_folder", enabled=False)
        return

    folder_to = f"{patch_folder}\\{model_type_path}\\"

    # Если папки нет в патче создаем ее
    if not os.path.exists(folder_to):
        os.makedirs(folder_to)

    # Получаем список файлов в папке Export
    files = os.listdir(folder_from)
    for file in files:
        delete_last_moved_files.lastMovedFiles.append(folder_to + file)
        shutil.move(os.path.join(folder_from, file), os.path.join(folder_to, file))

    dpg.configure_item("gr_move_files_to_path_folder", enabled=False)
    dpg.configure_item("gr_del_last_files", enabled=True)

    StatusBar.success_info("Files moved to patch folder.")


def move_icon_to_patch(wow_export_folder: str, patch_folder: str):
    icon_name = dpg.get_value("inp_icon_name_for_copy") + ".blp"
    if os.path.exists(wow_export_folder + "\\interface\\icons\\" + icon_name):
        if not os.path.exists(patch_folder + "\\interface\\icons\\"):
            os.makedirs(patch_folder + "\\interface\\icons\\")

        shutil.move(os.path.join(str(wow_export_folder) + "\\interface\\icons\\", icon_name),
                    os.path.join(str(patch_folder) + "\\interface\\icons\\", icon_name))
    else:
        possible_icon = "*" + icon_name.replace("inv_", "")[:-4] + "*"
        icons = glob.glob(wow_export_folder + "\\interface\\icons\\" + possible_icon)
        if len(icons) > 0:
            if not os.path.exists(patch_folder + "\\interface\\icons\\"):
                os.makedirs(patch_folder + "\\interface\\icons\\")

            for icon in icons:
                if os.path.exists(os.path.join(str(patch_folder) + "\\interface\\icons\\", os.path.basename(icon))):
                    os.remove(os.path.join(str(patch_folder) + "\\interface\\icons\\", os.path.basename(icon)))

                shutil.move(str(icon), patch_folder + "\\interface\\icons\\")
                last_icon_name = os.path.basename(icon).replace(".blp", "")

            dpg.set_value("inp_icon_name_for_copy", last_icon_name)
            dpg.configure_item("inp_icon_name_for_copy", width=len(last_icon_name) * 7.4,
                               pos=[(Config.WINDOW_WIDTH - len(last_icon_name) * 7.4) / 2.2, 180])
            dpg.configure_item("txt_left_arrows2", color=[250, 50, 0],
                               pos=[(Config.WINDOW_WIDTH - len(last_icon_name) * 7.4) / 2.2 - 25, 180])
            dpg.configure_item("txt_right_arrows2", color=[250, 50, 0],
                               pos=[dpg.get_item_pos("inp_icon_name_for_copy")[0] + dpg.get_item_width("inp_icon_name_for_copy") + 4, 180])


def move_textures_and_anims(file_path: str, model_type_path: str):
    wow_export_folder = reg_manager.wowExportFolder
    collections_folder = wow_export_folder + "\\item\\objectcomponents\\collections\\"
    model_name = "*" + dpg.get_value("inp_icon_name_for_copy")[4:].replace("helm_", "") + "*.blp"
    folder = os.path.dirname(file_path) + "\\"
    pre_folder = folder.replace("\\Export", "")

    files = os.listdir(pre_folder)
    for file in files:
        if file.endswith(".blp") or file.endswith(".anim"):
            shutil.move(os.path.join(pre_folder, file), os.path.join(folder, file))
    match model_type_path:
        case r"item\objectcomponents\head":
            other_textures = glob.glob(collections_folder + model_name)
            for texture in other_textures:
                shutil.move(str(texture), folder)


def overwrite_global_sequences(file_path: str, GlobalSeq_bytes: bytes):
    with open(file_path, "rb+") as file_m2:
        Binary.write_zeros(file_m2)
        last_offset = Binary.write_to_end(file_m2, GlobalSeq_bytes)
        Binary.write_zeros(file_m2)
        Binary.write_bytes(file_m2, M2Offsets.ofsGlobalSequences, last_offset.to_bytes(4, byteorder="little"))


def overwrite_nVies(file_path: str, nViews: int):
    with open(file_path, "rb+") as file_m2:
        nView_before = Binary.get_int_from_bytes(file_m2, 76)
        if nView_before < nViews:
            Binary.write_bytes(file_m2, 76, nViews.to_bytes(4, byteorder='little'))


def remove_exported_data(file_path: str):
    wow_export_folder = reg_manager.wowExportFolder
    file_name = os.path.basename(file_path)[:-3]
    name_pattern = f"({file_name})"
    folder = os.path.dirname(file_path) + "\\"
    target_folder = wow_export_folder + "\\" + folder.replace(wow_export_folder + "\\", "").replace("Export\\", "")
    files = os.listdir(target_folder)

    for file in files:
        if re.search(name_pattern, file, flags=re.I):
            os.unlink(os.path.join(target_folder, file))


def remove_lod(file_path: str):
    folder = os.path.dirname(file_path) + "\\"
    lod_files = glob.glob(folder + "*lod*.skin")
    for lod in lod_files:
        os.unlink(lod)


def rename_lod(file_path: str, nViews: int):
    folder = os.path.dirname(file_path) + "\\"
    if nViews == 1:
        remove_lod(file_path)
    else:
        for i in range(1, nViews):
            lod_file_list = glob.glob(folder + f"*_lod0{i}.skin")
            if lod_file_list:
                lod_file = lod_file_list[0]
                try:
                    os.rename(lod_file, lod_file.replace("_lod", ""))
                except FileExistsError:
                    pass

        remove_lod(file_path)


def rename_skins(file_path: str):
    folder = os.path.dirname(file_path) + "\\"
    skin_files = os.listdir(folder)
    for skin in skin_files:
        try:
            os.rename(os.path.join(folder, skin.lower()), os.path.join(folder, skin.lower().replace("_f0", "f0")))
        except (FileNotFoundError, FileExistsError):
            pass
        try:
            os.rename(os.path.join(folder, skin.lower()), os.path.join(folder, skin.lower().replace("_m0", "m0")))
        except (FileNotFoundError, FileExistsError):
            pass


def rename_race_items(model_type_path: str, file_path: str) -> str:
    if model_type_path == r"item\objectcomponents\head":
        rename_skins(file_path)

        if file_path.endswith("_m.m2"):
            try:
                os.rename(file_path, file_path.replace("_m.m2", "m.m2"))
                file_path = file_path.replace("_m.m2", "m.m2")
            except FileExistsError:
                pass

        if file_path.endswith("_f.m2"):
            try:
                os.rename(file_path, file_path.replace("_f.m2", "f.m2"))
                file_path = file_path.replace("_f.m2", "f.m2")
            except FileExistsError:
                pass

    return file_path


def select_model_type(sender: str):
    for checkbox in Config.ALL_CHECKBOXES:
        dpg.set_value(checkbox, True) if checkbox == sender else dpg.set_value(checkbox, False)

    match sender:
        case "chk_Ammo":
            Config.pathPrefix = "item\\objectcomponents\\ammo\\"
        case "chk_Collections":
            Config.pathPrefix = "item\\objectcomponents\\collections\\"
        case "chk_Doodads":
            Config.pathPrefix = "doodads\\"
        case "chk_Head":
            Config.pathPrefix = "item\\objectcomponents\\head\\"
        case "chk_Quiver":
            Config.pathPrefix = "item\\objectcomponents\\quiver\\"
        case "chk_Shield":
            Config.pathPrefix = "item\\objectcomponents\\shield\\"
        case "chk_Shoulder":
            Config.pathPrefix = "item\\objectcomponents\\shoulder\\"
        case "chk_Skybox":
            Config.pathPrefix = "environments\\stars\\"
        case "chk_Spell":
            Config.pathPrefix = "spells\\"
        case "chk_Weapon":
            Config.pathPrefix = "item\\objectcomponents\\weapon\\"
        case _:
            Config.pathPrefix = "creature\\"
