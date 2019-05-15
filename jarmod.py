#! /bin/bash/python3
# MIT License
#
# Copyright (c) 2019 Eduardo E. Betanzos Morales
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
from os import path
from os import linesep
from pathlib import Path
from internal import Modularizer
from internal import Compiler
import time


class Main:

    def __init__(self):
        self.__prod_name = "PyJarModularizer"
        self.__prod_version = "1.0.0"
        self.__copyright = "Copyright (c) 2019 Eduardo E. Betanzos Morales"
        self.__icon_copyright = "Icon made by monkik from www.flaticon.com"

        self.__descriptor_file = None
        self.__source_dir = None
        self.__dest_dir = None
        self.__jdk_home = None

    def main(self):
        # Construir el menú de ayuda
        help_description = f"Wellcome to {self.__prod_name}!\n------------------------------------------\nVersion: {self.__prod_version}"
        parser = ArgumentParser(description=help_description,
                                add_help=False,
                                prog="jarmod",
                                formatter_class=RawTextHelpFormatter,
                                epilog=self.__copyright + linesep + self.__icon_copyright)

        parser.add_argument("DESCRIPTOR", help="Path to modularization descriptor file")
        parser.add_argument("SOURCE", help="Path to directory containing source JAR files")

        parser.add_argument("--dest", metavar="<path>", help="Path to modularized JAR files destination directory. Will be created is not exist. Default is SOURCE/mods.")
        parser.add_argument("--module-path", metavar="<path>", help="Path to directories ans/or files containing depending modules")
        parser.add_argument("--jdk-home", metavar="<path>", help="Path to JDK root directory. By default current $JAVA_HOME will be used")
        parser.add_argument("--version", help="Display program version and exit", action="version", version=f"Version {self.__prod_version}")
        parser.add_argument("--help", "-h", action="help", help="Display this help and exit")

        # Parsear los parámetros
        args = parser.parse_args()

        # Validar los parámetros
        if not self.__validate_args(args):
            return

        # Iniciar el proceso
        modularizer = Modularizer(self.__descriptor_file, self.__source_dir, self.__dest_dir, self.__jdk_home, args.module_path)

        start_time = time.time()
        try:
            if not modularizer.start():
                # Si entra aquí significa que hubo errores durante el proceso, pero quizás algunos
                # JARs pudieron ser modularizados
                print("--------------------------------------------------------------------")
                print("  Process finish with some non fatal erros. Maybe some JAR files were modularized.")
            else:
                print()
                print("--------------------------------------------------------------------")
                print("  SUCCESSFUL!!")
        except Exception as e:
            print(e)
            print()
            print("--------------------------------------------------------------------")
            print("  Process finish with ERROR :(")

        end_time = time.time()

        print()
        print(f"  {modularizer.get_count_modularized()} JARs modularized in {self.__get_duration_str(start_time, end_time)}")
        print(f"  {modularizer.get_count_error_founds()} errors found")
        print()

    @classmethod
    def __get_duration_str(cls, start, end):
        total_duration_str = str(end - start)
        dot_index = total_duration_str.index(".")
        total_duration_int = int(total_duration_str[:dot_index])

        duration_list = []

        hours = total_duration_int // 3600
        if hours > 0:
            duration_list.append(str(hours))
            duration_list.append("h")
            duration_list.append(" ")

        minutes = (total_duration_int - hours * 3600) // 60
        if minutes > 0 or hours > 0:
            duration_list.append(str(minutes))
            duration_list.append("m")
            duration_list.append(" ")

        seconds = total_duration_int - (hours * 3600) - (minutes * 60)
        duration_list.append(str(seconds))
        duration_list.append(total_duration_str[dot_index:dot_index+4])
        duration_list.append("s")

        return "".join(duration_list)

    def __validate_args(self, args):
        # Validar que el descriptor exista y sea un archivo
        descriptor_path = args.DESCRIPTOR
        if not path.exists(descriptor_path):
            print("[ERROR] Descriptor file not exist (" + descriptor_path + ")")
            return False

        if not path.isfile(descriptor_path):
            print("[ERROR] Descriptor is not a file (" + descriptor_path + ")")
            return False

        self.__descriptor_file = Path(descriptor_path)

        # Validar que el directorio fuente exista y sea un directorio
        source_dir_path = args.SOURCE
        if not path.exists(source_dir_path):
            print("[ERROR] Source directory not exist (" + source_dir_path + ")")
            return False

        if not path.isdir(source_dir_path):
            print("[ERROR] Source is not a directory (" + source_dir_path + ")")
            return False

        self.__source_dir = Path(source_dir_path)

        # Validar que el directorio de destino existe y es un directorio
        # Solo si fue pasado como parámetro
        dest_dir_path = args.dest
        if dest_dir_path is not None:
            if path.exists(dest_dir_path):
                if path.isfile(dest_dir_path):
                    print("[ERROR] Destination is not a directory (" + dest_dir_path + ")")
                    return False
            else:
                self.__dest_dir = Path(dest_dir_path)
                self.__dest_dir.mkdir(parents=True)
        else:
            self.__dest_dir = Path(args.SOURCE, "mods")

        # Comprobar que el JDK_HOME es válido
        # Solo si fue pasado como parámetro
        jdk_home_path = args.jdk_home
        if jdk_home_path is not None:
            if not Compiler.is_valid_jdk_home(jdk_home_path):
                print("[WARN] Invalid JDK_HOME '" + jdk_home_path + "'. Default will be used.")
            else:
                self.__jdk_home = Path(jdk_home_path)

        # Si todo fue bien retorno True
        return True


# Definir punto de entrada de la aplicación si se ejecuta como script
if __name__ == "__main__":
    import sys
    sys.exit(Main().main())
