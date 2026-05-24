import dearpygui.dearpygui as dpg
import os
import winreg


class RegistryManager:
    def __init__(self):
        self.key = None
        self.key_str = winreg.REG_SZ
        self.key_int = winreg.REG_DWORD
        # Свойства
        self.alwaysOnTop = None
        self.autoDeleteExportedData = None
        self.autoFixGlobalSeq = None
        self.autoFixHelmOffset = None
        self.autoMoveFilesToPatch = None
        self.listfileFolder = None
        self.mpqEditorFolder = None
        self.patchFolder = None
        self.wowExportFolder = None

        self.init_options()

    def init_options(self):
        try:
            self.key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "SOFTWARE\\WoTLK_MultiTool", 0, access=winreg.KEY_ALL_ACCESS)

            self.alwaysOnTop = winreg.QueryValueEx(self.key, "alwaysOnTop")[0]
            self.autoDeleteExportedData = winreg.QueryValueEx(self.key, "autoDeleteExportedData")[0]
            self.autoFixGlobalSeq = winreg.QueryValueEx(self.key, "autoFixGlobalSeq")[0]
            self.autoFixHelmOffset = winreg.QueryValueEx(self.key, "autoFixHelmOffset")[0]
            self.autoMoveFilesToPatch = winreg.QueryValueEx(self.key, "autoMoveFilesToPatch")[0]
            self.listfileFolder = winreg.QueryValueEx(self.key, "ListFileFolderPath")[0]
            self.mpqEditorFolder = winreg.QueryValueEx(self.key, "mpqEditorFolderPath")[0]
            self.patchFolder = winreg.QueryValueEx(self.key, "patchFolderPath")[0]
            self.wowExportFolder = winreg.QueryValueEx(self.key, "wowExportFolderPath")[0]
        except FileNotFoundError:
            self.key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, "SOFTWARE\\WoTLK_MultiTool", 0, access=winreg.KEY_ALL_ACCESS)

            self.alwaysOnTop = 0
            self.autoDeleteExportedData = 0
            self.autoFixGlobalSeq = 1
            self.autoFixHelmOffset = 1
            self.autoMoveFilesToPatch = 1
            self.listfileFolder = ""
            self.mpqEditorFolder = ""
            self.patchFolder = f"C:\\Users\\{os.getlogin()}\\Desktop\\Patch-Ruru-Z.MPQ"
            self.wowExportFolder = f"C:\\Users\\{os.getlogin()}\\wow.export"

            winreg.SetValueEx(self.key, "alwaysOnTop", 0, self.key_int, self.alwaysOnTop)
            winreg.SetValueEx(self.key, "autoDeleteExportedData", 0, self.key_int, self.autoDeleteExportedData)
            winreg.SetValueEx(self.key, "autoFixGlobalSeq", 0, self.key_int, self.autoFixGlobalSeq)
            winreg.SetValueEx(self.key, "autoFixHelmOffset", 0, self.key_int, self.autoFixHelmOffset)
            winreg.SetValueEx(self.key, "autoMoveFilesToPatch", 0, self.key_int, self.autoMoveFilesToPatch)
            winreg.SetValueEx(self.key, "listfileFolderPath", 0, self.key_str, self.listfileFolder)
            winreg.SetValueEx(self.key, "mpqEditorFolderPath", 0, self.key_str, self.mpqEditorFolder)
            winreg.SetValueEx(self.key, "patchFolderPath", 0, self.key_str, self.patchFolder)
            winreg.SetValueEx(self.key, "wowExportFolderPath", 0, self.key_str, self.wowExportFolder)
        finally:
            winreg.CloseKey(self.key)

    def save_options(self):
        # Сначала получаем значения из GUI
        alwaysOnTop_value = str(dpg.get_value("chk_alwaysOnTop"))
        autoDeleteExportedData_value = str(dpg.get_value("chk_auto_delete_exported_files"))
        autoFixGlobalSeq_value = str(dpg.get_value("chk_autoFix_globalSeq"))
        autoFixHelmOffset_value = str(dpg.get_value("chk_auto_fix_helm_offset"))
        autoMoveFilesToPatch_value = str(dpg.get_value("chk_auto_move_files_to_patch"))
        listfile_folder_value = os.path.normpath(dpg.get_value("inp_listfile_folder")).strip('"') if dpg.get_value(
            "inp_listfile_folder") else ''
        mpqEditor_folder_value = os.path.normpath(dpg.get_value("inp_mpqEditor_folder")).strip('"') if dpg.get_value(
            "inp_mpqEditor_folder") else ''
        patch_folder_value = os.path.normpath(dpg.get_value("inp_patch_folder")).strip('"')
        wowExport_folder_value = os.path.normpath(dpg.get_value("inp_wowExport_folder")).strip('"')

        self.key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, "SOFTWARE\\WoTLK_MultiTool", 0, access=winreg.KEY_ALL_ACCESS)

        winreg.SetValueEx(self.key, "alwaysOnTop", 0, self.key_int, self.int_from_bool(alwaysOnTop_value))
        winreg.SetValueEx(self.key, "autoDeleteExportedData", 0, self.key_int, self.int_from_bool(autoDeleteExportedData_value))
        winreg.SetValueEx(self.key, "autoFixGlobalSeq", 0, self.key_int, self.int_from_bool(autoFixGlobalSeq_value))
        winreg.SetValueEx(self.key, "autoFixHelmOffset", 0, self.key_int, self.int_from_bool(autoFixHelmOffset_value))
        winreg.SetValueEx(self.key, "autoMoveFilesToPatch", 0, self.key_int, self.int_from_bool(autoMoveFilesToPatch_value))
        winreg.SetValueEx(self.key, "listfileFolderPath", 0, self.key_str, listfile_folder_value)
        winreg.SetValueEx(self.key, "mpqEditorFolderPath", 0, self.key_str, mpqEditor_folder_value)
        winreg.SetValueEx(self.key, "patchFolderPath", 0, self.key_str, patch_folder_value)
        winreg.SetValueEx(self.key, "wowExportFolderPath", 0, self.key_str, wowExport_folder_value)

        winreg.CloseKey(self.key)
        self.init_options()

    @staticmethod
    def int_from_bool(txt: str) -> int:
        return int(txt == "True")


reg_manager = RegistryManager()
