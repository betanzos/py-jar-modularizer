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

from .entity import Artifact
from .exception import ParseException
from .compiler import Compiler
from .tda import Tree
from .tda import TreeNode
from pathlib import Path
import json
import zipfile
import os


class Modularizer:
    def __init__(self, descriptor_file: Path, source_dir: Path, destination_dir: Path, jdk_home_path: Path,
                 module_path):
        self.__descriptor_file = descriptor_file
        self.__source_dir = source_dir
        self.__destination_dir = destination_dir
        self.__jdk_home_path = jdk_home_path
        self.__module_path = module_path

        self.__artifact_set = {}
        self.__artifact_list = []
        self.__jar_files_list = []
        self.__count_modularized = 0
        self.__count_error_founds = 0

        self.__compiler = None

    def get_count_modularized(self):
        """
        :return: Permite obtener la cantidad de archivos modularizados
        """
        return self.__count_modularized

    def get_count_error_founds(self):
        """
        :return: Permite obtener la cantidad de errores no fatales encontrados durante el proceso de modularización.
                 Estos errores son aquellos relacionados con la modularización de algún archivo JAR en particular pero
                 que no impiden que se continúe el proceso con el resto de archivos.
        """
        return self.__count_error_founds

    def start(self):
        """
        Inicia el proceso de modularización.

        :return: True si el proceso terminó sin errores, False en caso contrario.
        :exception ParseException: Si ocurrió algún error deserializando el archivo descriptor de modularización
        """
        print()
        print("Starting modularization process...")
        print("--------------------------------------------------------------------")
        print()

        self.__parse_descriptor()

        if len(self.__artifact_set) == 0:
            print("Empty descriptor.")
            return False

        self.__jar_files_list = [f for f in self.__source_dir.iterdir() if f.is_file() and f.suffix == ".jar"]
        if len(self.__jar_files_list) == 0:
            print("There are no JAR files in source directory")
            return False

        self.__process_jars()

        return self.__count_error_founds == 0

    def __parse_descriptor(self):
        """
        Deserializa el archivo JSON descriptor de modularización.

        Para cargar los artefactos definidos en el descriptor se utiliza un Set para evitar los
        duplicados. Esto provoca que si un artefacto es definido múltiples veces solo se cargará
        solamente el primero de ellos. Un artefacto se considera duplicado si se repite el atributo
        'name'.

        :exception ParseException: Si ocurre algún error que impida la deserialización.
        """

        # Mecanismo para deserializar tomado de:
        # https://medium.com/@yzhong.cs/serialize-and-deserialize-complex-json-in-python-205ecc636caa

        try:
            descriptor_text = self.__descriptor_file.read_text()
            self.__artifact_set = set(map(Artifact.from_json, json.loads(descriptor_text)))
        except Exception as e:
            raise ParseException("[ERROR] Error parsing modularization descriptor file. " + str(e))

    def __process_jars(self):
        """
        Procesa los archivos JAR encontrados en el directorio {@code sourceDir} para generar su correspondiente JAR
        modularizado. La modularización solo se lleva a cabo con aquellos archivos para los cuales exista un entrada
        correspondiente en el descriptor de modularización.

        Las entradas en descriptor de modularización serán analizadas para determinar el orden en el cual deben ser
        procesados los JARs, teniendo en cuenta las dependencias entre ellos. Aquellos que menos niveles de dependencias
        tengan serán procesados primero y los que más niveles dependencias tengan de último. Cuando hablamos de niveles de
        dependencias nos referimos a que si el artefacto A depende de B y este a su vez depende de C, el primero en ser
        modularizado será C, luego B y por último A.

        Es importante aclarar que las únicas dependencias que cuentan para los fines explicados arriba son aquellas que
        hacen referncia a los módulos que deseamos crear (aquellos cuya definición está declarada en el descriptor de
        modularización), nunca las que referencian a terceros módulos ya existentes.
        """
        # Crear la instancia del compilador
        try:
            self.__compiler = Compiler()
            if self.__jdk_home_path is not None:
                self.__compiler.set_jdk_home(self.__jdk_home_path)
        except Exception as e:
            print("[ERROR] " + str(e))

        if self.__compiler.get_jdk_home() is None:
            # Si llega aquí es porque:
            # 1 - No se especificó la ruta del JDK a utilar o esta no es válida, y
            # 2 - No existe la variable de entorno JAVA_HOME
            print("[ERROR] JAVA_HOME enviroment variable is not defined.")
            return

        print("[INFO] Using JDK_HOME: " + str(self.__compiler.get_jdk_home().resolve()))
        print()

        # Antes de modularizar el JAR es necesario primero ordenar los artefactos de acuerdo a sus dependencias para
        # asegurarnos de que antes de modularizar un artefacto ya han sido modularizados todos aquellos de los que este
        # depende
        self.__sort_artifacts()

        # Modularizar cada uno de los JARs
        for artifact in self.__artifact_list:
            for file in self.__jar_files_list:
                if file.name == artifact.get_name():
                    if not self.__modularize_jar(file, artifact):
                        self.__count_error_founds += 1
                    break

    def __sort_artifacts(self):
        """
        Ordena artefactos definidos en el descriptor de modularización teniendo en cuenta las dependencias entre ellos.
        Aquellos artefactos que menos niveles de dependencias tengan terminarán siendo primeros que aquellos que más niveles
        dependencias tengan.

        Cuando hablamos de niveles de dependencias nos referimos a que si el artefacto A depende de B y este a su vez
        depende de C, primero irá C, luego B y por último A.

        Es importante aclarar que las únicas dependencias que cuentan para los fines explicados arriba son aquellas que
        hacen referncia a los módulos que deseamos crear (aquellos cuya definición está declarada en el descriptor de
        modularización), nunca las que referencian a terceros módulos ya existentes.

        Los artefectos ordenados serán agregados a self.__artifact_list.

        ImplNote: Para lograr este orden se agregan cada unos de los artefactos contenidos en self.__artifact_set
                  en un árbol de dependencias, quedando en los niveles superiores aquellos que más niveles de dependencias
                  tengan.
        """

        # Crear el árbol de dependencias con una raíz ficticia ya que no contiene datos. Esto
        # se hace para que todos los nodos con la misma profundidad en su decendencia se encuentren
        # al mismo nivel
        dependencies_tree = Tree(TreeNode(Artifact()))

        for artifact in self.__artifact_set:
            # Busco si en el árbol ya existe un artefacto que defina el mismo módulo que el
            # artefacto analizado. Si esto ocurre es porque se trata del mismo artefacto.
            artifact_node = dependencies_tree.find_node_by_data(artifact, Modularizer.__equals_artifact_by_module_name)

            # Si no es parte del árbol de dependencias creo un nuevo nodo
            if artifact_node is None:
                artifact_node = TreeNode(artifact)
                # Lo agrego como hijo de la raíz
                dependencies_tree.get_root().get_children().append(artifact_node)

            # Esto es un truco para poder utilizar la referencia artifactNode dentro de expresiones lambda
            # puesto que al no ser final o efectivamente final me lanza error
            # artifactNodeReference = AtomicReference<>(artifactNode)

            # Agregar como hijos los módulos de los que depende el artefacto actual y
            # que se encuentran definidos cómo módulos por otros artefactos
            requires_modules = artifact.get_module().get_requires_modules()
            if requires_modules is not None:
                for module_name in requires_modules:
                    # Busco si el módulo requerido es definido por alguno de los artefactos
                    module_founds = [a for a in self.__artifact_set if a.get_module().get_name() == module_name]
                    # Si encuentro el artefacto que lo define...
                    if len(module_founds) > 0:
                        # Tomo el primero encontrado
                        a = module_founds[0]
                        # Busco si el artefacto ya existe en el árbol de dependencias
                        require_module_node = dependencies_tree.find_node_by_data(a,
                                                                                  Modularizer.__equals_artifact_by_module_name)

                        if require_module_node is None:
                            # Si no existe agrego el artefacto encontrado como hijo del artefacto actual
                            artifact_node.get_children().append(TreeNode(a))
                        else:
                            # Si ya existe en el árbol...
                            current_artifact_level = dependencies_tree.get_node_level(artifact_node)
                            required_artifact_level = dependencies_tree.get_node_level(require_module_node)

                            # Si el nivel en que se encuentra el artefacto requerido es menor o igual
                            # que el nivel donde se encuentra el artefacto actual, se lo quito al padre
                            # y lo agrego como hijo del artefacto actual.
                            # En caso contrario no es necesario hacerlo ya que si el nivel del requerido
                            # es mayor, este será modularizado antes
                            if required_artifact_level <= current_artifact_level:
                                dependencies_tree.remove_subtree(require_module_node)
                                artifact_node.get_children().append(require_module_node)

        # Obtener el listado de ordenado de los artefactos según deben ser modularizados
        # Los primeros deben ser los que se hayan en el nivel más profundo
        tree_level = dependencies_tree.get_tree_level()
        i = tree_level
        while i > 0:
            nodes_at_level = dependencies_tree.get_nodes_at_level(i)
            for item in nodes_at_level:
                self.__artifact_list.append(item.get_data())
            i -= 1

    @classmethod
    def __equals_artifact_by_module_name(cls, a1, a2):
        if a1.get_module() is not None and a2.get_module() is not None:
            return a1.get_module().get_name() == a2.get_module().get_name()

        return False

    def __modularize_jar(self, file, artifact):
        """
        Modulariza el archivo JAR :file de acuerdo con la definición de módulo especificada en el descriptor de
        modularización.

        :param file: Ruta al archivo JAR a modularizar.
        :param artifact: Objeto que contiene los datos de la entrada correspondiente al archivo JAR en el descriptor de
                         modularización.

        :return True si la modularización se completó satisfactoriamente, False en caso contrario.
        """

        temp_artifact_dir = None
        jar_file = None

        try:
            jar_file = zipfile.ZipFile(file, "r")

            temp_artifact_dir = self.__destination_dir / (file.name + "-temp")
            try:
                temp_artifact_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                raise RuntimeError("Can not create temp dir '" + temp_artifact_dir + "'. " + str(e))

            # Validar que el jar no tenga al menos una definición de módulo
            if len([m for m in jar_file.namelist() if m.endswith("module-info.class")]) > 0:
                raise RuntimeError("JAR file contains al least one module definition.")

            # Extraer el contenido del archivo JAR
            # OJO: No se puede utilizar ZipFile.extractall() porque falla en Windows si la longitud de la ruta del
            #      archivo a crear es mayor que el límite definido por el sistema operativo
            for entry_path in jar_file.namelist():
                try:
                    jar_file.extract(member=entry_path, path=temp_artifact_dir)
                except FileNotFoundError as e:
                    # Si el mensaje de error inicia con '[Errno 2] No such file or directory: ' seguramente el error
                    # está relacionado con la longitud de la ruta del archivo a crear.
                    # Esto puede causar que no se pueda compilar el descriptor del módulo si este error impidió que
                    # se creara alguno de los paquetes que son exportados
                    if str(e).startswith("[Errno 2] No such file or directory: "):
                        path_err = str(e).replace("[Errno 2] No such file or directory: ", "")
                        print("[WARN] Was not possible to extract the JAR's entry with de following path: " + path_err)
                        print("[WARN] Maybe JAR file '" + file.name + "' can not be modularized.")
                    else:
                        raise e

            # Obtener todos los paquetes que contengan al menos un archivo .class
            # lo meto en un set para evitar duplicados
            non_empty_packages = set()
            for entry_path in [entry for entry in jar_file.namelist() if
                               not jar_file.getinfo(entry).is_dir() and entry.endswith(".class")]:
                last_slash_index = entry_path.rfind('/')
                non_empty_packages.add(entry_path[0:last_slash_index].replace("/", "."))

            # Generar el archivo module-info.class
            module_info_data = None
            try:
                module_info_data = self.__generate_module_descriptor(temp_artifact_dir, artifact.get_module(),
                                                                     non_empty_packages)
            except IOError as e:
                raise IOError("Error generating module descriptor. " + str(e))

            if module_info_data is None:
                raise RuntimeError("Can not to compile module-info.java")

            # Agregar el descriptor del módulo al JAR
            self._patch_jar(file, module_info_data)

            print("[INFO] '" + file.name + "' modularized to module '" + artifact.get_module().get_name() + "'")
            self.__count_modularized += 1
            return True
        except IOError as e:
            print("[ERROR] I/O error modularizing JAR file '" + file.name + "'. " + str(e))
        except Exception as e:
            print("[ERROR] Unexpected error modularizing JAR file '" + file.name + "'. " + str(e))
        finally:
            if jar_file is not None:
                jar_file.close()

            if temp_artifact_dir is not None:
                try:
                    self.__recursive_remove(temp_artifact_dir)
                except Exception as e:
                    print("[WARN] Error while remove temp dir '" + temp_artifact_dir.name + "'. " + str(e))

        return False

    def __recursive_remove(self, path):
        try:
            if path.is_dir():
                for entry in path.iterdir():
                    self.__recursive_remove(entry)

                path.rmdir()
            else:
                path.unlink()
        except:
            raise RuntimeError("Can not remove " + ("file " if path.is_file() else "directory ") + path.resolve())

    def __generate_module_descriptor(self, output_dir, module, jar_non_empty_packages):
        """
        Genera el descriptor del módulo 'module' en el directorio definido por 'output_dir'.

        El proceso inicia creando la definición del descriptor del módulo, un archivo module-info.java. Para agregar las
        directivas 'exports' se utiliza la definición hecha en el descriptor de modularización. Si dicha definición no
        fue hecha entonces se agregará una directiva 'exports' para todos los paquetes del JAR original que contengan
        al menos un archivo '.class'. Para agregar las directivas 'requires' se utilizará la definición hecha en el
        descriptor de modularización y en caso de no existir no se agregará ninguna directiva de este tipo.

        Una vez creado el descriptor del módulo (archivo module-info.java) este es compilado utilido el jdk sobre el
        cual se está ejecutando este programa.

        El proceso de compilación puede fallar si los módulos de los cuales depende este módulo (según las directivas
        'requires' definidas) no son visibles por el compilador. Por defecto se agrega al comando de compilación el
        parámetro '--module-path <destDir>', donde 'destDir' es el directorio donde se depositarán los nuevos JARs
        modularizados, el cual fue definido utilizando parámetro '--dest' de este programa. Esto nos asegura que si
        el modulo que estamos modularizando actualmente depende de algún otro módulo que vamos a modularizar, este sea
        visible para el compilador (esto requiere que primero se modularice el módulo del cual se depende y luego se
        modularice este). Si adicionalmente el módulo a modularizar depende de otros ya existentes se puede utilizar
        el parámetro '--module-path' al ejecutar la aplicación para agregar cualquier otro directorio y/o archivos
        (este parámetro tiene la misma sintaxis del homónimo en 'java', 'javac', 'jlink' y demás herramientas del JDK).

        :param output_dir: Directorio en donde se debe generar el archivo module-info.java. Debe ser el directorio raíz en
                         el cual se extrajo el contenido del archivo JAR a modularizar.
        :param module: Objeto con la definición del módulo.
        :param jar_non_empty_packages: Listado de los paquetes contenidos en el archivo JAR que al menos contiene una archivo
                                   .class. Si 'module.exportsPackages == null' se agregará una entrada del tipo
                                   'exports package.name' para cada uno de los elementos de este listado.

        :return: Cotenido del archivo module-info.class correspondiente al archivo module-info.java compilado.

        :except IOError: Si ocurre un error escribiendo el archivo module-info.java en el disco duro.
        """

        # Crear el contenido del descriptor
        module_descriptor = ["module ", module.get_name(), " {", os.linesep]

        # Por defecto se exportarán todos aquellos paquetes que contengan archivos de clase
        final_packages_list = jar_non_empty_packages

        # Si se ha especificado explícitamente los paquetes a exportar estos serán los que se
        # agregarán al descriptor del módulo
        if module.get_exports_packages() is not None:
            final_packages_list = module.get_exports_packages()

        for p in final_packages_list:
            module_descriptor.append("    exports ")
            module_descriptor.append(p)
            module_descriptor.append(";")
            module_descriptor.append(os.linesep)

        if module.get_requires_modules() is not None:
            for m in module.get_requires_modules():
                module_descriptor.append("    requires ")
                module_descriptor.append(m)
                module_descriptor.append(";")
                module_descriptor.append(os.linesep)

        module_descriptor.append("}")

        # Escribir el descriptor en el disco duro
        try:
            (output_dir / "module-info.java").write_text("".join(module_descriptor))
        except:
            raise

        # Compilar el descriptor
        try:
            errors = self.__compiler.compile_module_descriptor(output_dir, str(self.__destination_dir) + (
                os.pathsep + self.__module_path if self.__module_path is not None else ""))
            if errors is not None:
                print(errors)
        except Exception as e:
            print("[ERROR] " + str(e))

        # Leer el descriptor compilado
        descriptor_data = None

        try:
            descriptor_data = (output_dir / "module-info.class").read_bytes()
        except Exception as e:
            print("[ERROR] " + str(e))

        return descriptor_data

    def _patch_jar(self, jar_file_path, module_descriptor_data):
        """
        Agrega la entrada /module-info.class al archivo JAR cuya ruta es 'jar_file_path'. El contenido de la entrada
        será 'module_descriptor_data'.

        :param jar_file_path: Archivo JAR a parchar
        :param module_descriptor_data: Contenido de la entrada /module-info.class
        """
        mod_jar_file = None
        try:
            # Hago una copia exacta del JAR
            mod_jar_file_path = self.__destination_dir / (jar_file_path.name + "-mod.jar")
            mod_jar_file_path.write_bytes(jar_file_path.read_bytes())

            # Agrego a la copia del archivo JAR original el descriptor del módulo
            mod_jar_file = zipfile.ZipFile(mod_jar_file_path, mode="a")
            mod_jar_file.writestr("module-info.class", module_descriptor_data)
        except Exception as e:
            RuntimeError("Error to patching original jar file. " + str(e))
        finally:
            if mod_jar_file is not None:
                mod_jar_file.close()
