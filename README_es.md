# PyJarModularizer
Este es el hermano pythonero del proyecto [JarModularizer](https://github.com/betanzos/jar-modularizer). Es un herramienta ligera de línea de comandos de python para hacer archivos JAR no modulares compatibles con el Java Platform Module System. Es una traducción del código de [JarModularizer](https://github.com/betanzos/jar-modularizer) con muchos cambios, ya que python en muy diferente a java.

## Uso
El modo en que PyJarModularizer trabaja es simple y casi idéntico a como lo hace [JarModularizer](https://github.com/betanzos/jar-modularizer). Necesita de un archivo JSON de configuración, llamado [descriptor de modularización](#formato-del-descriptor-de-modularización), que contiene la descripción de cómo cada archivo JAR, llamado artefacto, será convertido en un módulo de java, la ruta al directorio fuente en el cual podremos encontrar los archivos JAR no modulares; y la ruta al JDK que deseamos utilizar.

### Pre-requisitos
* [JDK 9 o superior](https://www.oracle.com/technetwork/java/javase/overview/index.html) ya que es requerido para compilar los decriptores de módulos.
* [Python 3.7](https://www.python.org/).

### Ejemplo
Desde python:
```
python jarmod.py DESCRIPTOR SOURCE --jdk-home /path/to/jdk
```
Utilizando un ejecutable (ir a [dist](dist)):
```
jarmod DESCRIPTOR SOURCE --jdk-home /path/to/jdk
```
El comando anterior depositará copias de los nuevos archivos JAR modulares en el directorio `SOURCE/mods` con el siguiente patrón de nombre: original.jar-mod.jar (ej. for log4j-1.2.17.jar el nombre del nuevo archivó será log4j-1.2.17.jar-mod.jar).

***Nota:*** si el parámetro ```--jdk-home``` no es pasado, se buscará la ruta al JDK en la variable de entorno JAVA_HOME.

#### ¡Importante!
Solo aquellos archivos cuyo nombre (incluida la extensión .jar) coincidan con una entrada en el [descriptor de modularización](#formato-del-descriptor-de-modularización) serán procesados.

## Creando un ejecutable (opcional)
Si se desea crear un ejecutable nativo (como los que encontramos en [dist](dist)) para cualquier plataforma (Windows, Linux y Mac OS X), se puede utilizar la herramineta [PyInstaller](https://www.pyinstaller.org/) (o cualquier otra compatible con Python 3.7).

### Instalar PyInstaller
El modo más sencillo de hacerlo es desde PyPI:
```
pip install pyinstaller
```

### Construyendo el ejecutable
Para empaquetar todo el proyecto en un único archivo ejecutable debemos utilizar el siguiente comando: (ver [exe-build-commands.txt](exe-build-commands.txt))

_Windows_
```
pyinstaller --onefile --name jarmod-<version>-win<arch> --icon icon\jigsaw-64.ico jarmod.py
```
_Linux y Mac OS X (Mac OS X teóricamente)_
```
pyinstaller --onefile --name jarmod-<version>-<osname><arch> jarmod.py
```
Consultar la [documentación oficial](https://pyinstaller.readthedocs.io/en/stable/) de PyInstaller para más detalles y opciones.

## Obteniendo ayuda
Si se pasa el comando `--help`, la ayuda de la herramienta será mostrada en la terminal.

## Formato del descriptor de modularización
Como se mencionó arriba, el descriptor de modularización es un archivo JSON. Debajo el formato de este.

***Nota:*** El formato JSON no permite comentarios, por lo que los comentarios en línea tipo Java se muestra solo con fines descriptivos.
```
[
    {
        "name": "log4j-1.2.17.jar",// nombre del artefacto
        "module": {// module entry
            "name": "log4j",// nombre del futuro módulo
            "exportsPackages": [// (opcional) lista de los paquetes del artefacto a ser exportados por el futuro módulo. Por defecto son todos los paquetes no vacíos del artefacto
                "org.apache.log4j",
                "org.apache.log4j.net"
            ],
            "requiresModules": [// (opcional) lista de las directivas requires a incluir en el archivo module-info.java. Por defecto ninguna directiva será incluida
                "java.base",
                "java.desktop",
                "java.management",
                "java.naming",
                "java.sql",
                "java.xml"
            ]
        }
    },
    ...
]
```

## Autor
Eduardo Betanzos [@ebetanzosm](https://twitter.com/ebetanzosm)

## Licencia
Este proyecto está licenciado bajo la Licencia del  MIT - para más detalles ver el archivo [LICENSE](LICENSE).