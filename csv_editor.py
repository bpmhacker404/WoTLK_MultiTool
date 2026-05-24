from typing import BinaryIO

import asyncio
import csv
import dearpygui.dearpygui as dpg
import json
import os
import pyperclip
import subprocess

from dbcpy.dbc_file import DBCFile
from dbc_records.creature_model_data import CreatureModelDataRecord
from dbc_records.creature_sound_data import CreatureSoundDataRecord
from dbc_records.light import LightRecord
from dbc_records.light_params import LightParamsRecord
from dbc_records.light_skybox import LightSkyBoxRecord
from dbc_records.footstep_terrain_lookup import FootstepTerrainLookupRecord
from dbc_records.npc_sounds import NPCSoundsRecord
from dbc_records.object_effect import ObjectEffectRecord
from dbc_records.object_effect_group import ObjectEffectGroupRecord
from dbc_records.object_effect_package import ObjectEffectPackageRecord
from dbc_records.object_effect_package_elem import ObjectEffectsPackageElemRecord
from dbc_records.particle_color import ParticleColorRecord
from dbc_records.sound_entries import SoundEntriesRecord
from dbc_records.sound_entries_advanced import SoundEntriesAdvancedRecord
from dbc_records.spell_record import SpellRecord
from dbc_records.spell_icon import SpellIconRecord
from dbc_records.spell_visual import SpellVisualRecord
from dbc_records.spell_visual_effect_name import SpellVisualEffectNameRecord
from dbc_records.spell_visual_kit import SpellVisualKitRecord
from dbc_records.spell_visual_kit_model_attach import SpellVisualKitModelAttachRecord

from utils.async_manager import async_manager
from utils.config import Config
from utils.registry import reg_manager
from utils.statusbar import StatusBar

DBC_RECORDS = {
    'over_creaturemodeldata.dbc': CreatureModelDataRecord,
    'over_creaturesounddata.dbc': CreatureSoundDataRecord,
    'over_light.dbc': LightRecord,
    'over_lightparams.dbc': LightParamsRecord,
    'over_lightskybox.dbc': LightSkyBoxRecord,
    'over_footstepterrainlookup.dbc': FootstepTerrainLookupRecord,
    'over_npcsounds.dbc': NPCSoundsRecord,
    'over_objecteffect.dbc': ObjectEffectRecord,
    'over_objecteffectgroup.dbc': ObjectEffectGroupRecord,
    'over_objecteffectpackage.dbc': ObjectEffectPackageRecord,
    'over_objecteffectpackageelem.dbc': ObjectEffectsPackageElemRecord,
    'over_particlecolor.dbc': ParticleColorRecord,
    'over_soundentries.dbc': SoundEntriesRecord,
    'over_soundentriesadvanced.dbc': SoundEntriesAdvancedRecord,
    'over_spell.dbc': SpellRecord,
    'over_spellicon.dbc': SpellIconRecord,
    'over_spellvisualeffectname.dbc': SpellVisualEffectNameRecord,
    'over_spellvisualkit.dbc': SpellVisualKitRecord,
    'over_spellvisualkitmodelattach.dbc': SpellVisualKitModelAttachRecord,
    'over_spellvisual.dbc': SpellVisualRecord,
}

BLIZZLIKE_ID = {
    'charhairgeosets.csv': 446,
    'creaturemodeldata.csv': 3440,
    'creaturesounddata.csv': 3108,
    'emotestextsound.csv': 566,
    'footstepterrainlookup.csv': 424,
    'light.csv': 2538,
    'lightfloatband.csv': 5502,
    'lightintband.csv': 16506,
    'lightparams.csv': 917,
    'lightskybox.csv': 148,
    'npcsounds.csv': 336,
    'objecteffect.csv': 828,
    'objecteffectgroup.csv': 611,
    'objecteffectpackage.csv': 491,
    'objecteffectpackageelem.csv': 844,
    'particlecolor.csv': 586,
    'soundentries.csv': 18019,
    'soundentriesadvanced.csv': 3627,
    'spellicon.csv': 4375,
    'spellvisual.csv': 16679,
    'spellvisualeffectname.csv': 7087,
    'spellvisualkit.csv': 15542,
    'spellvisualkitmodelattach.csv': 4696,
    'zoneintromusictable.csv': 601,
    'zonemusic.csv': 574,
}

CreatureDisplayInfo = {1: 'CreatureModelData.json', 2: 'CreatureSoundData.json', 3: 'CreatureDisplayInfoExtra.json',
                       12: 'NPCSounds.json', 13: 'ParticleColor.json', 15: 'ObjectEffectPackage.json', }
CreatureModelData = {13: 'CreatureSoundData.json', }
CreatureSoundData = {1: 'SoundEntries.json', 2: 'SoundEntries.json', 3: 'SoundEntries.json', 4: 'SoundEntries.json',
                     6: 'SoundEntries.json', 10: 'SoundEntries.json', 11: 'SoundEntries.json', 13: 'SoundEntries.json',
                     14: 'SoundEntries.json', 15: 'SoundEntries.json', 16: 'SoundEntries.json', 17: 'SoundEntries.json',
                     18: 'SoundEntries.json', 19: 'SoundEntries.json', 23: 'SoundEntries.json', 24: 'SoundEntries.json',
                     25: 'SoundEntries.json', 26: 'SoundEntries.json', 27: 'SoundEntries.json', 28: 'SoundEntries.json',
                     29: 'SoundEntries.json', 30: 'SoundEntries.json', }
FootstepTerrainLookup = {3: 'SoundEntries.json', 4: 'SoundEntries.json', }
Light = {7: 'LightParams.json', 8: 'LightParams.json', 9: 'LightParams.json', 10: 'LightParams.json', }
LightParams = {2: 'LightSkyBox.json', }
ObjectEffect = {2: 'ObjectEffectGroup.json', 6: 'SoundEntries.json', }
ObjectEffectPackageElem = {1: 'ObjectEffectPackage.json', 2: 'ObjectEffectGroup.json', }
SoundEntries = {29: 'SoundEntriesAdvanced.json', }
SoundEntriesAdvanced = {1: 'SoundEntries.json', }
Spell = {129: 'SpellVisual.json', 130: 'SpellVisual.json', 131: 'SpellIcon.json', 132: 'SpellIcon.json', }
SpellVisual = {1: 'SpellVisualKit.json', 2: 'SpellVisualKit.json', 3: 'SpellVisualKit.json', 4: 'SpellVisualKit.json',
               5: 'SpellVisualKit.json', 6: 'SpellVisualKit.json', 8: 'SpellVisualEffectName.json', 11: 'SoundEntries.json',
               12: 'SoundEntries.json', 14: 'SpellVisualKit.json', 15: 'SpellVisualKit.json', 22: 'SpellVisualKit.json',
               23: 'SpellVisualKit.json', 24: 'SpellVisualKit.json', 25: 'SpellVisualKit.json',
               }
SpellVisualKit = {3: 'SpellVisualEffectName.json', 4: 'SpellVisualEffectName.json', 5: 'SpellVisualEffectName.json',
                  6: 'SpellVisualEffectName.json', 7: 'SpellVisualEffectName.json', 8: 'SpellVisualEffectName.json',
                  14: 'SpellVisualEffectName.json', 15: 'SoundEntries.json', }
SpellVisualKitModelAttach = {1: 'SpellVisualKit.json', 2: 'SpellVisualEffectName.json'}

JSON_REQUiRED = {
    'creaturedisplayinfo.csv': CreatureDisplayInfo,
    'creaturesounddata.csv': CreatureSoundData,
    'creaturemodeldata.csv': CreatureModelData,
    'footstepterrainlookup.csv': FootstepTerrainLookup,
    'light.csv': Light,
    'lightparams.csv': LightParams,
    'npcsounds.csv': 'SoundEntries.json',
    'objecteffect.csv': ObjectEffect,
    'objecteffectpackageelem.csv': ObjectEffectPackageElem,
    'soundentries.csv': SoundEntries,
    'soundentriesadvanced.csv': SoundEntriesAdvanced,
    'spell.csv': Spell,
    'spellvisual.csv': SpellVisual,
    'spellvisualkit.csv': SpellVisualKit,
    'spellvisualkitmodelattach.csv': SpellVisualKitModelAttach,
}

JSON_NOT_REQUIRED = (
    'creaturemodeldata.csv',
    'creaturesounddata.csv',
    'light.csv',
    'lightparams.csv',
    'lightskybox.csv',
    'npcsounds.csv',
    'objecteffect.csv',
    'objecteffectgroup.csv',
    'objecteffectpackage.csv',
    'objecteffectpackageelem.csv',
    'particlecolor.csv',
    'soundentries.csv',
    'soundentriesadvanced.csv',
    'spellicon.csv',
    'spellvisualeffectname.csv',
    'spellvisual.csv',
    'spellvisualkit.csv',
)


def convert_str_to_int(id_value: str) -> int | None:
    try:
        return int(dpg.get_value(id_value))
    except ValueError:
        match id_value:
            case "inp_from":
                StatusBar.error_info("ERROR: FROM id must be integer.")
            case "inp_to":
                StatusBar.error_info("ERROR: TO id must be integer.")
            case "inp_offset":
                StatusBar.error_info("ERROR: OFFSET id must be integer.")
        return


def csv_paste_button():
    StatusBar.clear_info()
    text_from_clipboard = pyperclip.paste().strip('"')
    dpg.set_value("inp_csv", text_from_clipboard)


def csv_reader(_input_file: str) -> str:
    with open(_input_file, mode='r', newline='', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        for row in reader:
            yield row
            Config.current_position += 1


def csv_writer(_output_file: str, data: str):
    with open(_output_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_ALL)
        writer.writerows(data)


async def edit_csv():
    StatusBar.clear_info()

    dpg.set_value("inp_csv", dpg.get_value("inp_csv").strip('"'))
    input_file = dpg.get_value("inp_csv")
    min_value = dpg.get_value("inp_from")
    max_value = dpg.get_value("inp_to")
    offset_value = dpg.get_value("inp_offset")
    if input_file == "":
        StatusBar.error_info("ERROR: Enter the path to the csv file.")
        return
    elif not os.path.basename(input_file).lower().endswith(".csv"):
        StatusBar.error_info("ERROR: Select the csv file.")
        return
    elif not os.path.exists(input_file):
        StatusBar.error_info("ERROR: File not found.")
        return

    # * Настройка ezWoW интеграции в зависимости от csv
    if offset_value == "":
        csv_name = os.path.basename(input_file).lower()
        _column_id = dpg.get_value("inp_column")
        if csv_name in JSON_REQUiRED and csv_name in JSON_NOT_REQUIRED and _column_id == "1":
            Config.ezwowIntegration = True
            Config.idRelationship = False
        elif csv_name in JSON_REQUiRED and csv_name in JSON_NOT_REQUIRED and _column_id != "1":
            Config.ezwowIntegration = True
            Config.idRelationship = True
        elif csv_name in JSON_REQUiRED and _column_id != "1":
            Config.ezwowIntegration = True
            Config.idRelationship = True
        elif csv_name in JSON_REQUiRED and _column_id == "1":
            Config.ezwowIntegration = True
            Config.idRelationship = False
        elif csv_name in JSON_NOT_REQUIRED and _column_id == "1":
            Config.ezwowIntegration = True
            Config.idRelationship = False
        else:
            Config.ezwowIntegration = False
            Config.idRelationship = False
            StatusBar.error_info("ERROR: 2Auto integration is not possible. Do it manually.")
            return
    else:
        Config.ezwowIntegration = False
        Config.idRelationship = False
        offset_value = convert_str_to_int("inp_offset")

    if max_value == "":
        max_value = float('inf')
    else:
        max_value = convert_str_to_int("inp_to")

    # ? определяем последнее доступное id (blizzlike)
    if min_value == "":
        last_free_id = get_last_blizzlike_free_id()
        if last_free_id is None and not Config.idRelationship:
            StatusBar.error_info("ERROR: For auto ezWoW integration choose another column id or do it manually.")
            return
        elif Config.idRelationship:
            min_value = 0
        else:
            min_value = last_free_id
    else:
        min_value = convert_str_to_int("inp_from")

    # ? ------------------------------------------------------- Определяем столбцы -------------------------------------------------------
    column_id = dpg.get_value("inp_column")
    if ',' in column_id and '-' in column_id:
        StatusBar.error_info("ERROR: Wrong column id range.")
        return
    elif "-" in column_id:
        try:
            column_id = int(column_id.split("-")[0]), int(column_id.split("-")[1])
        except ValueError:
            StatusBar.error_info("ERROR: COLUMN id must be integer.")
            return
    elif "," in column_id:
        try:
            column_id = set(int(c_id) - 1 for c_id in column_id.split(","))
        except ValueError:
            StatusBar.error_info("ERROR: COLUMN id must be integer.")
            return
    elif column_id == "":
        StatusBar.error_info("ERROR: Enter COLUMN ID.")
        return
    else:
        try:
            column_id = int(column_id)
        except ValueError:
            StatusBar.error_info("ERROR: COLUMN id must be integer.")
            return

    # Получаем список строк и столбцов
    get_rows_and_columns_in_csv(input_file)

    # Анимация загрузки
    StatusBar.enable_loading()
    async_manager.run_unique_task(StatusBar.loading(" Reading the file "))

    await write_new_file(input_file, min_value, max_value, offset_value, column_id)


def ezwow_integration_with_relationships(_row_id: int, target_value: int) -> int | None:
    csv_name = os.path.basename(dpg.get_value("inp_csv")).lower()
    ezwow_integration_folder = get_ezwow_integration_folder()
    dict_value = JSON_REQUiRED[csv_name]
    if type(dict_value) == str:
        id_relationship_json = os.path.join(ezwow_integration_folder, dict_value)
    else:
        if _row_id in dict_value:
            id_relationship_json = os.path.join(ezwow_integration_folder, dict_value[_row_id])
        else:
            return target_value

    # Если в ezWoW_integration по какой-то причине нет нужного json
    if not os.path.exists(id_relationship_json):
        Config.csvErrors += 1
        StatusBar.error_info(f"{os.path.basename(id_relationship_json)} not found in 'ezWoW_integration' folder.")
        return

    with open(id_relationship_json, 'r') as id_json:
        id_relationship_dict = json.load(id_json)

    if str(target_value) in id_relationship_dict:
        Config.csvEditedValues += 1
        Config.csvCheckedValues += 1
        return id_relationship_dict[str(target_value)]
    else:
        Config.csvCheckedValues += 1
        return target_value


def ezwow_integration_without_relationships(target_value: int, ezwow_ids_list: set) -> int:
    if target_value in ezwow_ids_list:
        Config.csvConflictValues += 1
        updated_value = target_value
        while updated_value in ezwow_ids_list:
            updated_value += 1

        ezwow_ids_list.add(updated_value)
        Config.csvOldNewIds[target_value] = updated_value
        target_value = updated_value
        Config.csvEditedValues += 1

    else:
        Config.csvOldNewIds[target_value] = target_value

    Config.csvCheckedValues += 1
    return target_value


async def format_csv_pre():
    _input_file = dpg.get_value("inp_csv")
    if not _input_file.endswith(".csv"):
        StatusBar.error_info("ERROR: Select the csv file.")
        return
    if not os.path.exists(_input_file):
        StatusBar.error_info("ERROR: File not found.")
        return

    root_folder = os.path.dirname(_input_file)
    if not os.path.exists(new_folder := os.path.join(root_folder, "formated_csv")):
        os.mkdir(new_folder)
    edited_csv = os.path.join(new_folder, os.path.basename(_input_file))

    get_rows_and_columns_in_csv(_input_file)

    StatusBar.enable_loading()
    async_manager.run_unique_task(StatusBar.loading(" Formating the file "))

    await format_csv(_input_file, edited_csv)


async def format_csv(_input_file: str, edited_csv: str):
    csv_name = os.path.basename(_input_file)
    all_data = []
    for rows in csv_reader(_input_file):
        new_line = []
        for _line in rows:
            new_line.append(_line.replace("\n", ""))

            await asyncio.sleep(0)

        all_data.append(new_line)

    try:
        csv_writer(edited_csv, all_data)
        StatusBar.success_info(f"{csv_name} formatted successfully.")
    except PermissionError:
        StatusBar.error_info("ERROR: Permission denied. Unable to write file to disk.")
        return


def get_ezWoW_folder() -> str | None:
    ezWoW_folder = os.path.join(os.path.dirname(os.path.dirname(reg_manager.patchFolder)), "ezWoW")
    _ezWoW_dbc_patch = os.path.join(ezWoW_folder, "dbc_diff.MPQ")
    if os.path.exists(_ezWoW_dbc_patch) and os.path.isfile(reg_manager.mpqEditorFolder):
        return _ezWoW_dbc_patch
    else:
        StatusBar.error_info("ERROR: Enter correct paths for MPQEditor and your patch folder in the settings.")


def get_ezwow_integration_folder() -> str:
    config_folder = os.path.join(os.getcwd(), "ezWoW_integration")
    if not os.path.exists(config_folder):
        os.mkdir(config_folder)
    return config_folder


def get_free_id():
    StatusBar.clear_info()

    input_file = dpg.get_value("inp_csv").strip('"')
    min_value = dpg.get_value("inp_from")
    if input_file == "":
        StatusBar.error_info("ERROR: Enter the path to the csv file.")
        return
    elif not os.path.basename(input_file).lower().endswith(".csv"):
        StatusBar.error_info("ERROR: Select the csv file.")
        return

    csv_name = os.path.basename(dpg.get_value("inp_csv"))
    ezWoW_dbc_name = "over_" + csv_name.replace(".csv", ".dbc").lower()
    if not ezWoW_dbc_name in DBC_RECORDS:
        StatusBar.error_info("ERROR: This dbc is not supported.")
        return
    else:
        ezwow_ids_list = get_id_set_from_dbc(ezWoW_dbc_name, DBC_RECORDS[ezWoW_dbc_name])

    if ezwow_ids_list == "empty":
        StatusBar.error_info("ERROR: Failed to extract ezWoW dbc.")
        return

    if min_value == "":
        last_free_id = get_last_blizzlike_free_id()
    else:
        try:
            min_value = int(min_value)
            last_free_id = min_value
        except ValueError:
            StatusBar.error_info("ERROR: FROM id must be integer.")
            return

    while last_free_id in ezwow_ids_list:
        last_free_id += 1

    StatusBar.success_info(f"{last_free_id} copied to clipboard.")
    pyperclip.copy(last_free_id)


def get_id_set_from_dbc(_dbc: str, _dbc_record: BinaryIO) -> set | str:
    ezWoW_dbc_patch = get_ezWoW_folder()
    subprocess.run(f'{reg_manager.mpqEditorFolder} extract "{ezWoW_dbc_patch}" DBFilesClient\\{_dbc} ezWoW_integration /fp')
    extracted_ezwow_dbc = os.path.join(os.getcwd(), "ezWoW_integration\\DBFilesClient\\" + _dbc)
    if os.path.exists(extracted_ezwow_dbc):
        with open(extracted_ezwow_dbc, mode='rb') as f:
            dbc_file = DBCFile.from_file(f, _dbc_record)
            dbc_iterator = dbc_file.records
            return {iterator_item.id for iterator_item in dbc_iterator}
    else:
        return "empty"


def get_last_blizzlike_free_id() -> int | None:
    dbc = os.path.basename(dpg.get_value("inp_csv")).lower()
    if dbc in BLIZZLIKE_ID:
        return BLIZZLIKE_ID[dbc] + 1
    else:
        return None


def get_rows_and_columns_in_csv(_input_file: str):
    Config.dbcTotalRows = 0
    Config.current_position = 0
    with open(_input_file, mode='r', newline='', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        _ = next(reader)  # пропускаем заголовок
        Config.dbcTotalRows = sum(1 for _ in reader) + 1


def parsing(_row_id: int, _line: str, _min_value: int, _max_value: int, _offset_value: int, ezwow_ids_list: set) -> str:
    # * _row_id передается как ключ для словаря JSON_REQUiRED
    if _offset_value:
        try:
            target_value = int(_line)
            if _min_value <= target_value <= _max_value:
                Config.csvEditedValues += 1
                return target_value + _offset_value
            else:
                return _line
        except ValueError:
            return _line.replace("\n", "")

    # ? ezWoW integration
    else:
        try:
            target_value = int(_line)
            if _min_value <= target_value <= _max_value:
                if Config.idRelationship:
                    target_value = ezwow_integration_with_relationships(_row_id, target_value)
                else:
                    target_value = ezwow_integration_without_relationships(target_value, ezwow_ids_list)
                return target_value
            else:
                return _line

        except ValueError:
            return _line.replace("\n", "")


def save_updated_ids():
    json_name = os.path.basename(dpg.get_value("inp_csv")).replace(".csv", ".json")
    ezwow_integration_folder = get_ezwow_integration_folder()
    json_file = os.path.join(ezwow_integration_folder, json_name)
    with open(json_file, "w") as json_file:
        json.dump(Config.csvOldNewIds, json_file, indent=2)

    Config.csvOldNewIds.clear()


async def write_new_file(_input_file: str, _min_value: int, _max_value: int, _offset_value: int, _column_id: int):
    Config.csvEditedValues = 0
    Config.csvCheckedValues = 0
    Config.csvConflictValues = 0
    Config.csvErrors = 0
    root_folder = os.path.dirname(_input_file)
    if not os.path.exists(new_folder := os.path.join(root_folder, "edited_csv")):
        os.mkdir(new_folder)

    edited_csv = os.path.join(new_folder, os.path.basename(_input_file))

    if Config.ezwowIntegration and not Config.idRelationship:
        csv_name = os.path.basename(dpg.get_value("inp_csv"))
        ezWoW_dbc_name = "over_" + csv_name.replace(".csv", ".dbc").lower()
        if not ezWoW_dbc_name in DBC_RECORDS:
            StatusBar.error_info("ERROR: Auto integration is not possible. Do it manually.")
            return
        else:
            ezwow_ids_list = get_id_set_from_dbc(ezWoW_dbc_name, DBC_RECORDS[ezWoW_dbc_name])
    else:
        ezwow_ids_list = None

    if ezwow_ids_list == "empty":
        StatusBar.error_info("ERROR: Failed to extract ezWoW dbc.")
        return

    # Список всех строк
    all_data = []
    # если столбец целое число
    if isinstance(_column_id, int):
        column_id = _column_id - 1
        range_id = None
    # если столбец диапазон
    elif isinstance(_column_id, tuple):
        column_id = None
        range_id = tuple(range(_column_id[0] - 1, _column_id[-1]))
    elif isinstance(_column_id, set):
        range_id = _column_id
        column_id = None

    for rows in csv_reader(_input_file):
        new_line = []
        # Построковый перебор
        for _row_id, line in enumerate(rows):
            # если столбец целое число
            if _row_id == column_id:
                new_line.append(parsing(_row_id, line, _min_value, _max_value, _offset_value, ezwow_ids_list))
            # если столбец диапазон
            elif not range_id is None and _row_id in range_id:
                new_line.append(parsing(_row_id, line, _min_value, _max_value, _offset_value, ezwow_ids_list))
            else:
                new_line.append(line)

            await asyncio.sleep(0)

        # Добавляем строку в список всех строк
        all_data.append(new_line)

    # Запись в файл
    try:
        csv_writer(edited_csv, all_data)
    except PermissionError:
        StatusBar.error_info("ERROR: Permission denied. Unable to write file to disk.")
        return

    # Если в процессе выполнения произошли ошибки
    if Config.csvErrors > 0:
        return

    if Config.csvConflictValues > 0 and Config.csvEditedValues > 0:
        StatusBar.success_info(f"Total {Config.csvCheckedValues} ids checked / {Config.csvConflictValues} conflicts fixed.")
    elif Config.csvConflictValues == 0 and Config.csvEditedValues > 0:
        StatusBar.success_info(f"Total {Config.csvCheckedValues} ids checked / {Config.csvEditedValues} ids edited.")
    else:
        StatusBar.success_info(f"Total {Config.csvCheckedValues} ids checked. There are no conflicts here.")
    if Config.ezwowIntegration and not Config.idRelationship and Config.csvConflictValues > 0:
        save_updated_ids()
