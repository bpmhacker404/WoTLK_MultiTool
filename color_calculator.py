import dearpygui.dearpygui as dpg
import struct

from utils.statusbar import StatusBar


class ColorCalculator:
    @staticmethod
    def color_output():
        StatusBar.clear_info()

        r, g, b, _ = dpg.get_value("color_picker")
        r = round(r)
        g = round(g)
        b = round(b)
        x = round(r / 255.0, 6)
        y = round(g / 255.0, 6)
        z = round(b / 255.0, 6)

        dpg.set_value("inp_x_color", x)
        dpg.set_value("inp_y_color", y)
        dpg.set_value("inp_z_color", z)

        rgb = f"{r},{g},{b}"
        hex_color = ''.join([f"{int(i):02x}" for i in rgb.split(',')])
        dec_color = (r * 256 + g) * 256 + b
        dpg.set_value("inp_hex_color", hex_color)
        dpg.set_value("inp_dec_color", dec_color)
        dpg.set_value("inp_hex_bytes", ColorCalculator.hex_to_hex(hex_color))

    @staticmethod
    def dec_to_hex():
        StatusBar.clear_info()

        try:
            dec_color = int(dpg.get_value("inp_dec_color"))
            hex_color = hex(dec_color)[2:]

            dpg.set_value("inp_hex_color", hex_color)

            r = (dec_color >> 16) & 255
            g = (dec_color >> 8) & 255
            b = dec_color & 255

            dpg.set_value("color_picker", (r, g, b))

            x = round(r / 255.0, 6)
            y = round(g / 255.0, 6)
            z = round(b / 255.0, 6)

            dpg.set_value("inp_x_color", x)
            dpg.set_value("inp_y_color", y)
            dpg.set_value("inp_z_color", z)
            dpg.set_value("inp_hex_bytes", ColorCalculator.hex_to_hex(hex_color))
        except ValueError:
            if len(dpg.get_value("inp_dec_color")) > 0:
                StatusBar.error_info("ERROR: Invalid dec code.")

    @staticmethod
    def hex_to_dec():
        StatusBar.clear_info()

        hex_color = dpg.get_value("inp_hex_color")
        try:
            dec_color = int(hex_color, 16)
            dpg.set_value("inp_dec_color", dec_color)

            r = (dec_color >> 16) & 255
            g = (dec_color >> 8) & 255
            b = dec_color & 255

            dpg.set_value("color_picker", (r, g, b))

            x = round(r / 255, 4)
            y = round(g / 255, 4)
            z = round(b / 255, 4)

            dpg.set_value("inp_x_color", x)
            dpg.set_value("inp_y_color", y)
            dpg.set_value("inp_z_color", z)
            dpg.set_value("inp_hex_bytes", ColorCalculator.hex_to_hex(hex_color))

        except ValueError:
            if len(hex_color) > 0:
                StatusBar.error_info("ERROR: Invalid hex# code.")

    @staticmethod
    def hex_to_hex(hex_color: str) -> str:
        StatusBar.clear_info()

        try:
            r = round(int(hex_color[0:2], 16) / 255.0, 6)
            g = round(int(hex_color[2:4], 16) / 255.0, 6)
            b = round(int(hex_color[4:6], 16) / 255.0, 6)
            rgb_bytes = struct.pack("fff", r, g, b)
            HEX_string = rgb_bytes.hex().upper()
            return HEX_string
        except ValueError:
            StatusBar.error_info("ERROR: Invalid hex# code.")
