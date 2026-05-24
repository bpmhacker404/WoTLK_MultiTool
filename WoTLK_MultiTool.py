from threading import Thread

import dearpygui.dearpygui as dpg
import keyboard
import pyperclip
import re

from arrays_keyframes import (create_nBones_pre, create_nColor_pre, create_nGlobalSeq_pre, create_nMaterials_pre,
                              create_nTextureAnimation_pre, create_nTextureCombiner_pre, create_nTextures_pre, create_nTransparency_pre)
from color_calculator import ColorCalculator
from convert_autotexture import (auto_texture_pre, check_auto_move_files_to_patch, delete_last_moved_files, get_icon_name,
                                 move_files_to_patch_pre, select_model_type)
from csv_editor import edit_csv, format_csv_pre, get_free_id, csv_paste_button
from particle_cloner import ParticleCloner, particle_cloner_init
from position_scale import model_moving_pre, model_resize_pre
from texture_components import auto_convert_textures_pre, move_texture_components_pre, rename_texture_components

from utils.async_manager import async_manager, run_async_thread
from utils.config import Config
from utils.miscellaneous import (check_model_path, download_listfile, get_exported_model, open_patch_folder, open_wowexport_folder,
                                 open_file, open_skin, run_wow)
from utils.registry import reg_manager
from utils.statusbar import StatusBar


def mouse_click(_, app_data: tuple):
    if app_data[0] == 1:
        text_value = dpg.get_value(app_data[1])
        text_source = dpg.get_item_user_data(app_data[1])
        if text_value and text_source != "INP" and text_source != "move_position" and text_source != "scale_percent":
            StatusBar.clear_info()
            pyperclip.copy(text_value)
            StatusBar.copied_info(text_source)

        match text_source:
            case "move_position" | "scale_percent":
                dpg.set_value(app_data[1], -dpg.get_value(app_data[1]))

    elif app_data[0] == 2:
        text_source = dpg.get_item_user_data(app_data[1])
        clipboard_value = pyperclip.paste()
        match text_source:
            case "#":
                if len(clipboard_value) <= 6:
                    dpg.set_value(app_data[1], clipboard_value)
                    ColorCalculator.hex_to_dec()
            case "DEC":
                if len(clipboard_value) <= 8:
                    dpg.set_value(app_data[1], clipboard_value)
                    ColorCalculator.dec_to_hex()
            case "INP":
                dpg.set_value(app_data[1], clipboard_value)
                try_define_model_type()
            case "INP_cloner" | "CSV":
                dpg.set_value(app_data[1], clipboard_value)
            case "move_position" | "scale_percent":
                dpg.set_value(app_data[1], 0)


def press_paste_btn():
    dpg.set_value("inp_model", pyperclip.paste().strip('"'))
    try_define_model_type()


def save_options():
    reg_manager.save_options()

    if reg_manager.autoMoveFilesToPatch:
        dpg.configure_item("gr_move_files_to_path_folder", enabled=False)
        dpg.configure_item("btn_move", label="AUTO MOVE TO PATCH 'ENABLED'")
    else:
        dpg.configure_item("gr_move_files_to_path_folder", enabled=False)
        dpg.configure_item("btn_move", label="MOVE FILES TO PATCH FOLDER")

    dpg.set_viewport_always_top(bool(reg_manager.alwaysOnTop))

    dpg.delete_item("win_settings")


def show_options():
    if not dpg.does_item_exist("win_settings"):
        with dpg.window(no_resize=True, no_collapse=True, tag="win_settings", pos=[4, 5], width=Config.WINDOW_WIDTH - 23,
                        height=Config.WINDOW_HEIGHT - 48, no_move=True, label="Settings",
                        on_close=lambda: dpg.delete_item("win_settings"), ):
            dpg.add_text(r"""
         _       __    ________    __ __    __  ___      ____  _ ______            __
        | |     / /___/_  __/ /   / //_/   /  |/  /_  __/ / /_(_)_  __/___  ____  / /
        | | /| / / __ \/ / / /   / ,<     / /|_/ / / / / / __/ / / / / __ \/ __ \/ / 
        | |/ |/ / /_/ / / / /___/ /| |   / /  / / /_/ / / /_/ / / / / /_/ / /_/ / /  
        |__/|__/\____/_/ /_____/_/ |_|  /_/  /_/\__,_/_/\__/_/ /_/  \____/\____/_/   
                    
                                                                            version 1.3
                    """)

            dpg.add_separator(label="Path to the export folder from wow.export")
            dpg.add_input_text(tag="inp_wowExport_folder", width=630)
            dpg.set_value("inp_wowExport_folder", reg_manager.wowExportFolder)
            dpg.add_separator(label="Path to your current patch folder")
            dpg.add_input_text(tag="inp_patch_folder", width=630)
            dpg.set_value("inp_patch_folder", reg_manager.patchFolder)
            dpg.add_separator(label="Path to your listfile folder")
            dpg.add_input_text(tag="inp_listfile_folder", width=630)
            dpg.set_value("inp_listfile_folder", reg_manager.listfileFolder)
            dpg.add_separator(label="Path to Ladik's MPQEditor.exe")
            dpg.add_input_text(tag="inp_mpqEditor_folder", width=630)
            dpg.set_value("inp_mpqEditor_folder", reg_manager.mpqEditorFolder)
            dpg.add_separator(label="Miscellaneous")
            dpg.add_checkbox(tag="chk_alwaysOnTop", label="Always on top")
            dpg.set_value("chk_alwaysOnTop", bool(reg_manager.alwaysOnTop))
            dpg.add_checkbox(tag="chk_autoFix_globalSeq", label="Auto fix global sequences")
            dpg.set_value("chk_autoFix_globalSeq", bool(reg_manager.autoFixGlobalSeq))
            dpg.add_checkbox(tag="chk_auto_fix_helm_offset", label="Auto fix helm offset")
            dpg.set_value("chk_auto_fix_helm_offset", bool(reg_manager.autoFixHelmOffset))
            dpg.add_checkbox(tag="chk_auto_delete_exported_files", label="Auto delete exported files")
            dpg.set_value("chk_auto_delete_exported_files", bool(reg_manager.autoDeleteExportedData))
            dpg.add_checkbox(tag="chk_auto_move_files_to_patch", label="Auto move files to patch")
            dpg.set_value("chk_auto_move_files_to_patch", bool(reg_manager.autoMoveFilesToPatch))
            dpg.add_button(tag="btn_save_options", label="Save", width=60, height=30,
                           pos=[Config.WINDOW_WIDTH - 170, Config.WINDOW_HEIGHT - 120], callback=save_options)
            dpg.add_button(tag="btn_cancel_options", label="Cancel", width=60, height=30,
                           pos=[Config.WINDOW_WIDTH - 100, Config.WINDOW_HEIGHT - 120], callback=lambda: dpg.delete_item("win_settings"))

            dpg.add_text(" " * 38 + "Coded by Sectym", pos=[5, Config.WINDOW_HEIGHT - 76])

        dpg.show_item("win_settings")


def try_define_model_type():
    try:
        check_model_path()
    except TypeError:
        pass

    input_text = dpg.get_value("inp_model")
    creature_keywords = ("creature", "mount", "dragon", "drake", "boss", "lord")
    creature_pattern = "(?:{})".format("|".join(creature_keywords))
    skybox_keywords = ("sky", "cloud", "aurora", "background", "stars")
    skybox_pattern = "(?:{})".format("|".join(skybox_keywords))
    spells_keywords = ("fx_", "_fx", "cfx_", "_aura", "spell")
    spells_pattern = "(?:{})".format("|".join(spells_keywords))
    weapon_keywords = ("weapon", "axe_", "bow_", "firearm_", "hammer_", "hand_", "knife_", "mace_", "misc_", "offhand_",
                       "polearm_", "stave_", "sword_", "thrown_", "totem_2h", "wand_", "glaive_", "staff_",)
    weapon_pattern = "(?:{})".format("|".join(weapon_keywords))
    shield_keywords = ("shield_", "shield")
    shield_pattern = "(?:{})".format("|".join(shield_keywords))
    head_keywords = ("helm_", "helm", "cap_", "hat_", "be_m", "be_f", "dr_m", "dr_f", "dw_m", "dw_f", "gn_m", "gn_f", "hu_m", "hu_f",
                     "ni_m", "ni_f", "or_m", "or_f", "ta_m", "ta_f", "tr_m", "tr_f", "sc_m", "sc_f", "bem.m2", "bef.m2", "drm.m2",
                     "drf.m2", "dwm.m2", "dwf.m2", "gnm.m2", "gnf.m2", "hum.m2", "huf.m2", "nim.m2", "nif.m2", "orm.m2", "orf.m2", "tam.m2",
                     "taf.m2", "trm.m2", "trf.m2", "scm.m2", "scf.m2")
    head_pattern = "(?:{})".format("|".join(head_keywords))
    shoulder_keywords = ("shoulder_", "shoulder", "_l.m2", "_r.m2")
    shoulder_pattern = "(?:{})".format("|".join(shoulder_keywords))
    quiver_keywords = ("quiver_", "quiver")
    quiver_pattern = "(?:{})".format("|".join(quiver_keywords))
    ammo_keywords = ("ammo_", "arrow_bow_")
    ammo_pattern = "(?:{})".format("|".join(ammo_keywords))
    collections_keywords = ("collections", "armor_", "boot_", "belt_", "chest_", "cloth_", "leather_", "mail_", "pant_", "plate_")
    collections_pattern = "(?:{})".format("|".join(collections_keywords))
    doodads_keywords = ("doodads", "expansion", "generic")
    doodads_pattern = "(?:{})".format("|".join(doodads_keywords))

    if re.search(spells_pattern, input_text, flags=re.I):
        possible_model_type = "chk_Spell"
    elif re.search(skybox_pattern, input_text, flags=re.I):
        possible_model_type = "chk_Skybox"
    elif re.search(weapon_pattern, input_text, flags=re.I):
        possible_model_type = "chk_Weapon"
    elif re.search(shield_pattern, input_text, flags=re.I):
        possible_model_type = "chk_Shield"
    elif re.search(shoulder_pattern, input_text, flags=re.I):
        possible_model_type = "chk_Shoulder"
    elif re.search(head_pattern, input_text, flags=re.I):
        possible_model_type = "chk_Head"
    elif re.search(quiver_pattern, input_text, flags=re.I):
        possible_model_type = "chk_Quiver"
    elif re.search(ammo_pattern, input_text, flags=re.I):
        possible_model_type = "chk_Ammo"
    elif re.search(collections_pattern, input_text, flags=re.I):
        possible_model_type = "chk_Collections"
    elif re.search(doodads_pattern, input_text, flags=re.I):
        possible_model_type = "chk_Doodads"
    elif re.search(creature_pattern, input_text, flags=re.I):
        possible_model_type = "chk_Creature"
    else:
        possible_model_type = "chk_Creature"

    select_model_type(possible_model_type)
    get_icon_name()


# // --------------------------------------------------------- Start ----------------------------------------------------------------------
keyboard.add_hotkey("shift+F1", get_exported_model, suppress=False)

delete_last_moved_files.lastMovedFiles = []  # lastMovedFiles - атрибут функции delete_last_moved_files

Thread(target=run_async_thread, daemon=True).start()
Thread(target=download_listfile, daemon=True).start()  # Скачиваем listfile

# * ------------------------------------------------------- GUI Config --------------------------------------------------------------------
dpg.create_context()
dpg.create_viewport(title="WoTLK MultiTool", resizable=False, large_icon="multitool.ico")
dpg.configure_viewport(0, width=Config.WINDOW_WIDTH, height=Config.WINDOW_HEIGHT)
dpg.set_viewport_max_width(Config.WINDOW_WIDTH)
dpg.set_viewport_max_height(Config.WINDOW_HEIGHT)

with dpg.font_registry():
    with dpg.font(r"C:\Windows\Fonts\consola.ttf", 13, default_font=True, tag="Default font") as font:
        pass
dpg.bind_font("Default font")

# MAIN WINDOW
with dpg.window(no_resize=True, no_title_bar=True, tag="win_main"):
    with dpg.group(horizontal=True, tag="gr_inp_txt"):
        dpg.add_input_text(tag="inp_model", width=571, hint="Path to the m2 model", user_data="INP", auto_select_all=True,
                           callback=try_define_model_type)
        dpg.add_button(tag="btn_paste", label="Paste", width=62, callback=press_paste_btn)
        dpg.add_spacer(height=25)

    # AUTO TEXTURE FROM MANIFEST
    dpg.add_separator(label="CONVERT / AUTO TEXTURE FROM MANIFEST")
    dpg.add_spacer(height=2)
    with dpg.group(horizontal=True, tag="gr_select_model_type"):
        dpg.add_text(" Select model type: ")
        dpg.add_checkbox(label="Creature", tag="chk_Creature", callback=select_model_type)
        dpg.add_spacer()
        dpg.add_checkbox(label="Spell", tag="chk_Spell", callback=select_model_type)
        dpg.add_spacer()
        dpg.add_checkbox(label="Skybox", tag="chk_Skybox", callback=select_model_type)
        dpg.add_spacer()
        dpg.add_checkbox(label="Weapon", tag="chk_Weapon", callback=select_model_type)
        dpg.add_spacer()
        dpg.add_checkbox(label="Shield", tag="chk_Shield", callback=select_model_type)
        dpg.add_spacer()
        dpg.add_checkbox(label="Head", tag="chk_Head", callback=select_model_type)
    with dpg.group(horizontal=True, tag="gr_auto_texture_from_manifest2"):
        dpg.add_spacer(width=160)
        dpg.add_checkbox(label="Shoulder", tag="chk_Shoulder", callback=select_model_type)
        dpg.add_spacer()
        dpg.add_checkbox(label="Ammo", tag="chk_Ammo", callback=select_model_type)
        dpg.add_spacer()
        dpg.add_checkbox(label="Quiver", tag="chk_Quiver", callback=select_model_type)
        dpg.add_spacer()
        dpg.add_checkbox(label="Collections", tag="chk_Collections", callback=select_model_type)
        dpg.add_spacer()
        dpg.add_checkbox(label="Doodads", tag="chk_Doodads", callback=select_model_type)
        dpg.add_spacer()

    dpg.add_spacer()

    with dpg.group(horizontal=True, tag="gr_auto_texture_from_manifest"):
        dpg.add_button(label="CONVERT / AUTO TEXTURE", tag="btn_start", width=315, height=27, callback=auto_texture_pre)
    with dpg.group(parent="gr_auto_texture_from_manifest", tag="gr_move_files_to_path_folder"):
        dpg.add_button(label="MOVE FILES TO PATCH FOLDER", tag="btn_move", width=315, height=27, callback=move_files_to_patch_pre)
    with dpg.group(horizontal=True, tag="gr_open_folders"):
        dpg.add_button(label="OPEN WOW.EXPORT FOLDER", tag="btn_wowexport_folder", width=315, height=27, callback=open_wowexport_folder)
        dpg.add_button(label="OPEN PATCH FOLDER", tag="btn_patch_folder", width=160, height=27, callback=open_patch_folder)
    with dpg.group(parent="gr_open_folders", tag="gr_del_last_files"):
        dpg.add_button(label="DELETE LAST FILES", tag="btn_delete_last_moved_files", width=147, height=27, callback=delete_last_moved_files)
        dpg.configure_item("gr_del_last_files", enabled=False)
    with dpg.group(horizontal=True, tag="gr_icon_path_output"):
        dpg.add_text(">>>", tag="txt_left_arrows2", pos=[165, 180])
        dpg.add_input_text(tag="inp_icon_name_for_copy", hint="---------ICON--NAME--FOR--COPY---------", user_data="Icon name",
                           auto_select_all=True, width=280)
        dpg.add_text("<<<", tag="txt_right_arrows2")
    with dpg.group(horizontal=True, tag="gr_model_path_output"):
        dpg.add_text(">>>", tag="txt_left_arrows", pos=[165, 210])
        dpg.add_input_text(tag="inp_model_name_for_copy", hint="-------MODEL---NAME---FOR---COPY-------", user_data="Model name",
                           auto_select_all=True, width=280)
        dpg.add_text("<<<", tag="txt_right_arrows")

    dpg.add_separator(label="CREATE ARRAYS / KEYFRAMES")
    dpg.add_spacer(height=2)

    # TEXTURECOMBINER
    with dpg.group(horizontal=True, parent="win_main", tag="gr_texture_combiner"):
        dpg.add_text(" nTextureCombiner")
        dpg.add_spacer(width=-1)
        dpg.add_input_text(tag="inp_nTextureCombiner", width=35)
        dpg.add_spacer(width=394)
        dpg.add_button(tag="btn_create_nTextureCombiner", label="Create", width=62, callback=create_nTextureCombiner_pre)
        dpg.add_spacer(height=20)

    # GLOBALSEQ
    with dpg.group(horizontal=True, parent="win_main", tag="gr_global_seq"):
        dpg.add_text(" nGlobalSeq")
        dpg.add_spacer(width=41)
        dpg.add_input_text(tag="inp_nGlobalSeq", width=35)
        dpg.add_spacer(width=394)
        dpg.add_button(tag="btn_create_nGlobalSeq", label="Create", width=62, callback=create_nGlobalSeq_pre)
        dpg.add_spacer(height=20)

    # BONES
    with dpg.group(horizontal=True, parent="win_main", tag="gr_bones"):
        dpg.add_text(" nBones")
        dpg.add_spacer(width=69)
        dpg.add_input_text(tag="inp_nBones", width=35)
        dpg.add_text(" nKeyFrames")
        dpg.add_input_text(tag="inp_nBones_keyframes", width=35)
        dpg.add_checkbox(tag="chk_Bones_Translation", label="Translation", default_value=False)
        dpg.add_checkbox(tag="chk_Bones_Rotation", label="Rotation", default_value=False)
        dpg.add_checkbox(tag="chk_Bones_Scale", label="Scale", default_value=False)
        dpg.add_spacer(width=5)
        dpg.add_button(tag="btn_create_nBones", label="Create", width=62, callback=create_nBones_pre)
        dpg.add_spacer(height=20)

    # COLOR
    with dpg.group(horizontal=True, parent="win_main", tag="gr_color"):
        dpg.add_text(" nColor")
        dpg.add_spacer(width=69)
        dpg.add_input_text(tag="inp_nColor", width=35)
        dpg.add_text(" nKeyFrames")
        dpg.add_input_text(tag="inp_nColor_keyframes", width=35)
        dpg.add_spacer(width=266)
        dpg.add_button(tag="btn_create_nColor", label="Create", width=62, callback=create_nColor_pre)
        dpg.add_spacer(height=20)

    # TEXTURES
    with dpg.group(horizontal=True, parent="win_main", tag="gr_textures"):
        dpg.add_text(" nTextures")
        dpg.add_spacer(width=48)
        dpg.add_input_text(tag="inp_nTextures", width=35)
        dpg.add_spacer(width=394)
        dpg.add_button(tag="btn_create_nTextures", label="Create", width=62, callback=create_nTextures_pre)
        dpg.add_spacer(height=20)

    # MATERIALS
    with dpg.group(horizontal=True, parent="win_main", tag="gr_materials"):
        dpg.add_text(" nMaterials")
        dpg.add_spacer(width=41)
        dpg.add_input_text(tag="inp_nMaterials", width=35)
        dpg.add_spacer(width=394)
        dpg.add_button(tag="btn_create_nMaterials", label="Create", width=62, callback=create_nMaterials_pre)
        dpg.add_spacer(height=20)

    # TRANSPARENCY
    with dpg.group(horizontal=True, parent="win_main", tag="gr_transparency"):
        dpg.add_text(" nTransparency")
        dpg.add_spacer(width=20)
        dpg.add_input_text(tag="inp_nTransparency", width=35)
        dpg.add_text(" nKeyFrames")
        dpg.add_input_text(tag="inp_nTransparency_keyframes", width=35)
        dpg.add_spacer(width=266)
        dpg.add_button(tag="btn_create_nTransparency", label="Create", width=62, callback=create_nTransparency_pre)
        dpg.add_spacer(height=20)

    # TEXTURE ANIMATION
    with dpg.group(horizontal=True, parent="win_main", tag="gr_texture_animation"):
        dpg.add_text(" nTextureAnimation")
        dpg.add_input_text(tag="inp_nTextureAnimation", width=35)
        dpg.add_text(" nKeyFrames")
        dpg.add_input_text(tag="inp_nTextureAnimation_keyframes", width=35)
        dpg.add_checkbox(tag="chk_TextureAnimation_Translation", label="Translation", default_value=True)
        dpg.add_checkbox(tag="chk_TextureAnimation_Rotation", label="Rotation", default_value=False)
        dpg.add_checkbox(tag="chk_TextureAnimation_Scale", label="Scale", default_value=False)
        dpg.add_spacer(width=5)
        dpg.add_button(tag="btn_create_nTextureAnimation", label="Create", width=62, callback=create_nTextureAnimation_pre)
        dpg.add_spacer(height=30)

    # OPEN M2 / SKIN FILES
    with dpg.group(horizontal=True, parent="win_main", tag="gr_open_btn"):
        dpg.add_spacer(width=80)
        dpg.add_button(tag="btn_open_file", label="OPEN M2 FILE", height=26, width=150, callback=open_file)
        dpg.add_button(tag="btn_open_skin", label="OPEN SKIN FILE(S)", height=26, width=150, callback=open_skin)
        dpg.add_button(tag="btn_run_wow", label="RUN 'WOW.EXE'", height=26, width=150, callback=run_wow)

    # COLOR CALCULATOR
    dpg.add_separator(label="COLOR CALCULATOR")
    dpg.add_spacer(height=2)
    with dpg.group(horizontal=True, parent="win_main", tag="gr_color_calculator"):
        dpg.add_color_edit((255, 255, 255), tag="color_picker", width=170, label="", no_alpha=True, callback=ColorCalculator.color_output)
        dpg.add_spacer(width=58)
        dpg.add_text("DEC")
        dpg.add_input_text(tag="inp_dec_color", hint="DEC", user_data="DEC", width=70, auto_select_all=True,
                           callback=ColorCalculator.dec_to_hex)
        dpg.add_text("HEX")
        dpg.add_input_text(tag="inp_hex_bytes", hint="HEX", user_data="HEX", auto_select_all=True, width=177)
    with dpg.group(horizontal=True, parent="win_main", tag="gr_color_xyz"):
        dpg.add_text(" #")
        dpg.add_input_text(tag="inp_hex_color", hint="#", width=58, user_data="#", auto_select_all=True,
                           callback=ColorCalculator.hex_to_dec)
        dpg.add_spacer(width=162)
        dpg.add_text("x")
        dpg.add_input_text(default_value="1", tag="inp_x_color", hint="x", user_data="x", auto_select_all=True, width=70)
        dpg.add_spacer(width=6)
        dpg.add_text("y")
        dpg.add_input_text(default_value="1", tag="inp_y_color", hint="y", user_data="y", auto_select_all=True, width=70)
        dpg.add_spacer(width=6)
        dpg.add_text("z")
        dpg.add_input_text(default_value="1", tag="inp_z_color", hint="z", user_data="z", auto_select_all=True, width=70)

    # MODEL POSITION / SCALE
    dpg.add_separator(label="MODEL POSITION / SCALE")
    dpg.add_spacer(height=2)
    with dpg.group(horizontal=True, parent="win_main", tag="gr_vertices"):
        dpg.add_text(" x")
        dpg.add_input_float(tag="inp_x_position", format="%.3f", step=0.01, step_fast=0.1, user_data="move_position", width=95)
        dpg.add_text("y")
        dpg.add_input_float(tag="inp_y_position", format="%.3f", step=0.01, step_fast=0.1, user_data="move_position", width=95)
        dpg.add_text("z")
        dpg.add_input_float(tag="inp_z_position", format="%.3f", step=0.01, step_fast=0.1, user_data="move_position", width=95)
        dpg.add_button(label="MOVE", tag="btn_move_vertices", width=60, callback=model_moving_pre)
        dpg.add_spacer(width=27)
        dpg.add_input_int(label=" %", tag="inp_scale_modifier", width=80, step_fast=10, user_data="scale_percent")
        dpg.add_spacer(width=0.5)
        dpg.add_button(label="RESIZE", tag="btn_resize", width=62, height=24, callback=model_resize_pre)

    dpg.add_spacer(height=2)

    # PARTICLE CLONER
    dpg.add_separator(label="PARTICLE CLONER")
    dpg.add_spacer(height=2)
    with dpg.group(horizontal=True, tag="gr_cloner_m2_from"):
        dpg.add_input_text(tag="inp_m2from", width=571, hint="Path to the source m2 model", user_data="INP_cloner", auto_select_all=True)
        dpg.add_button(tag="btn_paste_m2_from", label="Paste", width=62, callback=ParticleCloner.paste_btn_m2from)
        dpg.add_spacer(height=25)

    with dpg.group(horizontal=True, tag="gr_cloner_m2_to"):
        dpg.add_input_text(tag="inp_m2to", width=571, hint="Path to the target m2 model", user_data="INP_cloner", auto_select_all=True)
        dpg.add_button(tag="btn_paste_m2to", label="Paste", width=62, callback=ParticleCloner.paste_btn_m2to)
        dpg.add_spacer(height=25)

    with dpg.group(horizontal=True, tag="gr_cloner_chk1"):
        dpg.add_checkbox(tag="chk_save_already_exists", label="Save already exists particles", default_value=False)
        dpg.add_spacer(width=15)
        dpg.add_checkbox(tag="chk_identify_bones", label="Try to identify bones ids", default_value=False)
        dpg.add_spacer(width=35)
    dpg.add_button(tag="btn_copy_particles", label="Copy", width=62, height=30, pos=[Config.WINDOW_WIDTH - 83, Config.WINDOW_HEIGHT - 307],
                   callback=particle_cloner_init)

    with dpg.group(horizontal=True, tag="gr_cloner_chk2"):
        dpg.add_checkbox(tag="chk_do_not_copy_enabledin", label="Do not copy 'enabledin'", default_value=False)

    dpg.add_spacer(height=2)

    # TEXTURE COMPONENTS
    dpg.add_separator(label="TEXTURE COMPONENTS")
    dpg.add_spacer(height=2)
    with dpg.group(horizontal=True, parent="win_main", tag="gr_texture_components"):
        dpg.add_button(label="MOVE TEXTURES", tag="btn_move_texturecomponents", height=27, width=105, callback=move_texture_components_pre)
        dpg.add_button(label="FIX NAMES", tag="btn_fix_names", height=27, width=105, callback=rename_texture_components)
        dpg.add_spacer(width=22)
        dpg.add_checkbox(tag="chk_auto_blp_convert", label="Convert DXT5 to 256Color", default_value=True,
                         callback=auto_convert_textures_pre)
    with dpg.group(horizontal=True, parent="gr_texture_components", tag="gr_texture_components2"):
        dpg.add_checkbox(tag="chk_auto_reduce_png", label="Reduce large textures", default_value=True)

    dpg.add_spacer(height=2)

    # CSV EDITOR / EZWOW INTEGRATION
    dpg.add_separator(label="CSV EDITOR / EZWOW INTEGRATION")
    dpg.add_spacer(height=2)
    with dpg.group(horizontal=True, parent="win_main", tag="gr_csv_editor"):
        dpg.add_input_text(tag="inp_csv", width=571, hint="Path to the csv file", user_data="CSV", auto_select_all=True)
        dpg.add_button(tag="btn_csv_paste", label="Paste", width=62, callback=csv_paste_button)
        dpg.add_spacer(height=25)

    with dpg.group(horizontal=True, parent="win_main", tag="gr_csv_editor_range"):
        dpg.add_text(" FROM")
        dpg.add_input_text(tag="inp_from", width=70, hint="AUTO")
        dpg.add_text(" TO")
        dpg.add_input_text(tag="inp_to", width=70, hint="END")
        dpg.add_text(" OFFSET")
        dpg.add_input_text(tag="inp_offset", width=70, hint="AUTO")
        dpg.add_text(" COLUMN ID")
        dpg.add_input_text(tag="inp_column", width=85)
        dpg.add_spacer(width=37)
        dpg.add_button(tag="btn_edit", label="EDIT", width=62, height=25, callback=lambda: async_manager.run_unique_task(edit_csv()))

    with dpg.group(horizontal=True, parent="win_main", tag="gr_csv_editor_btn"):
        dpg.add_button(tag="btn_format", label="FORMAT CSV", width=90, height=25,
                       callback=lambda: async_manager.run_unique_task(format_csv_pre()))
        dpg.add_button(tag="btn_get_free_id", label="GET FREE ID", width=90, height=25, callback=get_free_id)
        dpg.add_spacer(height=30)

    # STATUSBAR
    dpg.add_button(label=" * ", pos=[Config.WINDOW_WIDTH - 50, Config.WINDOW_HEIGHT - 66], tag="btn_options", callback=show_options)
    dpg.add_text("", tag="txt_info", pos=(5, Config.WINDOW_HEIGHT - 66))

    with dpg.item_handler_registry(tag="hnd_mouse_click"):
        dpg.add_item_clicked_handler(callback=mouse_click)

    # Назначаем mouse click handler
    text_inputs = ("inp_hex_color",
                   "inp_dec_color",
                   "inp_hex_bytes",
                   "inp_x_color",
                   "inp_y_color",
                   "inp_z_color",
                   "inp_model",
                   "inp_m2from",
                   "inp_m2to",
                   "inp_csv",
                   "inp_x_position",
                   "inp_y_position",
                   "inp_z_position",
                   "inp_scale_modifier",
                   "inp_model_name_for_copy",
                   "inp_icon_name_for_copy",)

    for text_input in text_inputs:
        dpg.bind_item_handler_registry(text_input, "hnd_mouse_click")

    # Назначаем handler на пробел
    with dpg.handler_registry():
        dpg.add_key_press_handler(dpg.mvKey_Spacebar, callback=press_paste_btn)

    # Стартовые настройки GUI (значения из реестра)
    dpg.set_viewport_always_top(bool(reg_manager.alwaysOnTop))
    check_auto_move_files_to_patch()

dpg.set_exit_callback(async_manager.stop)
dpg.setup_dearpygui()
dpg.set_primary_window(window="win_main", value=True)
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
