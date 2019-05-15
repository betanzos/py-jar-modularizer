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

from pathlib import Path
import os
import subprocess

javac = "javac"
if os.name == "nt":
    javac = "javac.exe"


class Compiler:
    def __init__(self):
        self.__jdk_home = Path(os.environ.get("JAVA_HOME")) if os.environ.get("JAVA_HOME") is not None else None
        self.__jdk_bin_dir = None
        self.__build_jdk_bin_path()

    def __build_jdk_bin_path(self):
        """
        Construye la ruta al directorio contenedor de los binarios del JDK
        """
        if self.__jdk_home is not None:
            self.__jdk_bin_dir = self.__jdk_home / "bin"
        else:
            print("[WARN] JDK_HOME is none")

    def set_jdk_home(self, jdk_home):
        if not Compiler.is_valid_jdk_home(jdk_home):
            raise RuntimeError("Invalid JDK_HOME '" + jdk_home + "'")

        self.__jdk_home = jdk_home
        self.__build_jdk_bin_path()

    def get_jdk_home(self):
        return self.__jdk_home

    def compile_module_descriptor(self, target_module_dir, module_path):
        if self.__jdk_bin_dir is None:
            raise ValueError("Impossible to locate JDK_HOME/bin path for JDK_HOME: " + self.__jdk_home)

        # Construir el comando de compilación
        command_list = [str((self.__jdk_bin_dir / javac).resolve()), "-d", str(target_module_dir)]

        if module_path is not None:
            command_list.append("--module-path")
            command_list.append(module_path)

        command_list.append(str(target_module_dir / "module-info.java"))

        # Ejecutar el comando de compilación
        compiler_process = subprocess.run(command_list, text=True, stderr=subprocess.PIPE)
        # Si hay error de compilación devuelvo la salida de la consola de compilación
        if compiler_process.returncode is not 0:
            return "Command: " + self.__get_full_command_str(command_list) + os.linesep + compiler_process.stderr

    @classmethod
    def __get_full_command_str(cls, command_list):
        new_command_list = []

        first_entry = True
        for cmdEntry in command_list:
            if not first_entry:
                new_command_list.append(" ")

            first_entry = False
            new_command_list.append(cmdEntry)

        return "".join(new_command_list)

    @classmethod
    def is_valid_jdk_home(cls, jdk_home_path):
        """
        Permite conocer si el jdk_home_path} en un JAVA_HOME válido.

        Esto se hace coprobando únicamente que exista el archivo jdk_home_path/bin/java y que se tengan permisos de
        ejecución sobre este.

        :param jdk_home_path: Ruta al directorio raíz del JDK
        :return: True si existe el archivo javac dentro de la ruta jdk_home_path/bin/ y se tengan permisos de ejecución
                 sobre este, False caso contrario.
        """
        javac_path = Path(jdk_home_path, "bin", javac)
        return javac_path.exists() and javac_path.is_file() and os.access(javac_path, os.X_OK)
