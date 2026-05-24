import asyncio
import dearpygui.dearpygui as dpg
import math

from utils.async_manager import async_manager
from utils.config import Config

class StatusBar:
    @staticmethod
    def clear_info():
        Config.showLoading = False
        dpg.set_value("txt_info", "")

    @staticmethod
    def error_info(error_message: str):
        Config.showLoading = False
        if len(error_message) > 86:
            line = error_message[:87]
            dpg.configure_item("txt_info", color=[255, 10, 0], pos=[5, Config.WINDOW_HEIGHT - 66])
            dpg.set_value("txt_info", line)
            async_manager.run_unique_task(StatusBar.running_line(error_message))
        else:
            dpg.configure_item("txt_info", color=[255, 10, 0], pos=[5, Config.WINDOW_HEIGHT - 66])
            dpg.set_value("txt_info", error_message)

    @staticmethod
    def success_info(success_message: str):
        Config.showLoading = False
        if len(success_message) > 86:
            line = success_message[:87]
            dpg.configure_item("txt_info", color=[10, 255, 0], pos=[5, Config.WINDOW_HEIGHT - 66])
            dpg.set_value("txt_info", line)
            async_manager.run_unique_task(StatusBar.running_line(success_message))
        else:
            dpg.configure_item("txt_info", color=[10, 255, 0], pos=[5, Config.WINDOW_HEIGHT - 66])
            dpg.set_value("txt_info", success_message)

    @staticmethod
    def copied_info(copied_value: str):
        Config.showLoading = False
        dpg.configure_item("txt_info", color=[0, 240, 255], pos=[5, Config.WINDOW_HEIGHT - 66])
        dpg.set_value("txt_info", f"{copied_value} copied to clipboard")

    @staticmethod
    async def running_line(message: str):
        Config.showLoading = False
        await asyncio.sleep(1)

        while True:
            if len(message) > 86:
                message = message[1:]
                line = message[:87]
                dpg.set_value("txt_info", line)
                await asyncio.sleep(0.1)
            else:
                return

    @staticmethod
    async def loading(message: str):
        while True:
            for symbol in Config.loadingSymbols:
                if Config.showLoading:
                    try:
                        completed = math.floor(Config.current_position * 100 / Config.dbcTotalRows)
                    except ZeroDivisionError:
                        completed = 0
                    dpg.set_value("txt_info", symbol + message + str(completed) + " %")
                    await asyncio.sleep(0.2)
                else:
                    return

    @staticmethod
    async def converting_png(message: str):
        while True:
            for symbol in Config.loadingSymbols:
                if Config.showLoading:
                    if Config.totalToConvertTextures>0:
                        dpg.set_value("txt_info", symbol + message + str(Config.currentPng) + "/" + str(Config.totalToConvertTextures))
                    await asyncio.sleep(0.2)
                else:
                    return

    @staticmethod
    def enable_loading():
        Config.showLoading = True
        dpg.configure_item("txt_info", color=[255, 255, 255], pos=[5, Config.WINDOW_HEIGHT - 66])
