class Config:
    WINDOW_WIDTH, WINDOW_HEIGHT = 670, 1030
    pathPrefix = ""
    loadingSymbols = ("\\", "|", "/", "-")
    csvEditedValues = 0
    csvConflictValues = 0
    csvCheckedValues = 0
    current_position = 0
    current_png = 0
    total_to_convert_textures = 0
    dbcTotalRows = 0
    csvErrors = 0
    csvOldNewIds = {}
    ezwowIntegration = False
    idRelationship = False
    showLoading = False

    ALL_CHECKBOXES = ("chk_Ammo", "chk_Collections", "chk_Creature", "chk_Doodads", "chk_Head", "chk_Quiver", "chk_Shield", "chk_Shoulder",
                      "chk_Skybox", "chk_Spell", "chk_Weapon",)


# ? ---------------------------------------------------------------------------------------------------------------------------------------
r"""
python -m nuitka --standalone --onefile --onefile-tempdir-spec="{TEMP}/WoTLK_Multitool_Data" --windows-console-mode=disable --remove-output --include-data-files=C:\Users\bpmhacker\PycharmProjects\WoTLK_MultiTool\ICO.ico=multitool.ico --include-package=comtypes --nofollow-import-to=comtypes.test,comtypes.gen,cv2,cryptography,numpy,tkinter,pydoc --windows-icon-from-ico=C:\Users\bpmhacker\PycharmProjects\WoTLK_MultiTool\ICO.ico C:\Users\bpmhacker\PycharmProjects\WoTLK_MultiTool\WoTLK_MultiTool.py --output-dir=C:\Users\bpmhacker\Desktop 
"""

# // PIL Можно исключить
# _avif.cp313-win_amd64.pyd
# _avif.pyi
# _imagingft.cp313-win_amd64.pyd
# _imagingft.pyi
# _imagingmath.cp313-win_amd64.pyd
# _imagingmath.pyi
# _webp.cp313-win_amd64.pyd
# _webp.pyi
# _imagingtk.cp313-win_amd64.pyd
# _imagingtk.pyi
