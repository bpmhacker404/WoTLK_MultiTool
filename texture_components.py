from PIL import Image
from threading import Thread

import dearpygui.dearpygui as dpg
import os
import random
import shutil
import subprocess

from utils.async_manager import async_manager
from utils.config import Config
from utils.registry import reg_manager
from utils.statusbar import StatusBar


def auto_convert_textures_pre():
    auto_convert_blp = dpg.get_value("chk_auto_blp_convert")
    if not auto_convert_blp:
        dpg.set_value("chk_auto_reduce_png", False)
        dpg.configure_item("gr_texture_components2", enabled=False)
    else:
        dpg.configure_item("gr_texture_components2", enabled=True)


def auto_convert_textures(textures_: list):
    auto_reduce_png = dpg.get_value("chk_auto_reduce_png")
    processes_to_blp = []
    for png_texture in textures_:
        if auto_reduce_png:
            try:
                img_format = reduce_png_image(png_texture)
            except:
                img_format = "/FBLP_PAL_A8"
        else:
            img_format = "/FBLP_PAL_A8"

        p_blp = subprocess.Popen(["BLPConverter8.exe", img_format, png_texture], creationflags=subprocess.CREATE_NO_WINDOW,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        processes_to_blp.append(p_blp)

    for i, process_to_blp in enumerate(processes_to_blp):
        process_to_blp.wait()
        Config.current_png = i + 1


def generate_random_texture_name(old_name_: str) -> str:
    char_list = list(old_name_)
    random_numb = random.randint(0, 999)
    char_list.insert(-9, str(random_numb))
    return "".join(char_list)


def move_texture_components_pre():
    StatusBar.clear_info()
    Config.current_png = 0
    Config.total_to_convert_textures = 0
    StatusBar.enable_loading()
    async_manager.run_unique_task(StatusBar.converting_png(" Converting textures "))
    Thread(target=move_texture_components, daemon=True).start()


def move_texture_components():
    texture_components_folder = reg_manager.wowExportFolder + "\\item\\TEXTURECOMPONENTS\\"
    cape_textures_folder = reg_manager.wowExportFolder + "\\item\\objectcomponents\\cape\\"
    components_textures = 0
    cape_textures = 0
    auto_convert_blp = dpg.get_value("chk_auto_blp_convert")
    textures_for_convert = []
    textures_for_delete = []
    processes_to_png = []

    if not os.path.exists(texture_components_folder) and not os.path.exists(cape_textures_folder):
        StatusBar.error_info("ERROR: no textures found to move.")
        return

    # Проверяем есть ли в wow.export текстуры шмота
    if os.path.exists(texture_components_folder):
        for root, _, files in os.walk(texture_components_folder):
            founded_components_texture = len(files)
            if founded_components_texture > 0:
                components_textures += founded_components_texture
            if auto_convert_blp:
                for file in files:
                    textures_for_convert.append(os.path.join(root, file))

    # Проверяем есть ли в wow.export текстуры плащей
    if os.path.exists(cape_textures_folder):
        files = os.listdir(cape_textures_folder)
        founded_cape_texture = len(files)
        if founded_cape_texture > 0:
            cape_textures += founded_cape_texture
            if auto_convert_blp:
                for file in files:
                    textures_for_convert.append(os.path.join(cape_textures_folder, file))

    Config.total_to_convert_textures = components_textures + cape_textures

    # Если нужно конвертируем через BLPConverter8
    if auto_convert_blp and Config.total_to_convert_textures > 0:
        for blp_texture in textures_for_convert:
            png_texture = blp_texture.replace(".blp", ".png")
            textures_for_delete.append(png_texture)
            p_png = subprocess.Popen(["BLPConverter8.exe", "/FPNG_RGBA", blp_texture], creationflags=subprocess.CREATE_NO_WINDOW,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            processes_to_png.append(p_png)

        for process_to_png in processes_to_png:
            process_to_png.wait()

        auto_convert_textures(textures_for_delete)

        # Удаляем png после конвертации
        for png_texture in textures_for_delete:
            if os.path.exists(png_texture):
                os.remove(png_texture)

    # Если есть переносим в patch folder
    if components_textures > 0:
        destination_folder = reg_manager.patchFolder + "\\item\\TEXTURECOMPONENTS\\"
        shutil.copytree(texture_components_folder, destination_folder, dirs_exist_ok=True)
        shutil.rmtree(texture_components_folder)

    if cape_textures > 0:
        destination_folder = reg_manager.patchFolder + "\\item\\objectcomponents\\cape\\"
        shutil.copytree(cape_textures_folder, destination_folder, dirs_exist_ok=True)
        shutil.rmtree(cape_textures_folder)

    if components_textures > 0 or cape_textures > 0:
        StatusBar.success_info(f"{Config.total_to_convert_textures} textures moved to patch folder.")
    else:
        StatusBar.error_info("ERROR: no textures found to move.")


def rename_blp_texture(file: str) -> str:
    while not file.endswith("_u") and not file.endswith("_f") and not file.endswith("_m"):
        if len(file) > 1:
            file = file[:-1]
        else:
            return file + "_u.blp"
    else:
        return file + ".blp"


def reduce_png_image(image_path_: str) -> str:
    with Image.open(image_path_) as img:
        IMG_FORMAT_ = "/FBLP_PAL_A8"
        png_width, png_height = img.size
        if png_width >= 1024 or png_height >= 1024:
            IMG_FORMAT_ = "/FBLP_DXT3"
            new_size = (png_width // 2, png_height // 2)
            img = img.convert("RGBA")
            r, g, b, a = img.split()
            r = r.resize(new_size, Image.Resampling.LANCZOS)
            g = g.resize(new_size, Image.Resampling.LANCZOS)
            b = b.resize(new_size, Image.Resampling.LANCZOS)
            a = a.resize(new_size, Image.Resampling.LANCZOS)
            img = Image.merge('RGBA', (r, g, b, a))
            img.save(image_path_)

    return IMG_FORMAT_


def rename_texture_components():
    texture_components_folder = reg_manager.patchFolder + "\\item\\TEXTURECOMPONENTS\\"
    TEXTURE_COMPONENTS = ('armlowertexture', 'armuppertexture', 'foottexture', 'handtexture', 'leglowertexture', 'leguppertexture',
                          'torsolowertexture', 'torsouppertexture')
    if os.path.exists(texture_components_folder):
        renamed_texture = 0
        for root, _, files in os.walk(texture_components_folder):
            if root.rsplit("\\", 1)[1].lower() in TEXTURE_COMPONENTS:
                for file in files:
                    if (file.lower().endswith(".blp") and not file.lower().endswith("_u.blp") and not file.lower().endswith("_m.blp") and
                            not file.lower().endswith("_f.blp")):
                        new_name = rename_blp_texture(file)
                        try:
                            os.rename(os.path.join(root, file), os.path.join(root, new_name))
                        except FileExistsError:
                            new_name = generate_random_texture_name(new_name)
                            try:
                                os.rename(os.path.join(root, file), os.path.join(root, new_name))
                            except FileExistsError:
                                rename_texture_components()
                        except FileNotFoundError:
                            pass

                        renamed_texture += 1

        if renamed_texture == 0:
            StatusBar.error_info("ERROR: No textures need renaming.")
        else:
            StatusBar.success_info(f"{renamed_texture} textures renamed.")
    else:
        StatusBar.error_info("ERROR: patch folder does not contain TEXTURECOMPONENTS.")
