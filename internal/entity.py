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


class Module:
    def __init__(self, name: str, exportsPackages=None, requiresModules=None):
        self.__name = name
        self.__exports_packages = exportsPackages
        self.__requires_modules = requiresModules

    @classmethod
    def from_json(cls, data):
        return cls(**data)

    def get_name(self):
        return self.__name

    def get_exports_packages(self):
        return self.__exports_packages

    def get_requires_modules(self):
        return self.__requires_modules


class Artifact:
    def __init__(self, name=None, module=None):
        self.__name = name
        if isinstance(module, dict):
            self.__module = Module.from_json(module)
        else:
            self.__module = module

    @classmethod
    def from_json(cls, data):
        return cls(**data)

    def get_name(self):
        return self.__name

    def get_module(self):
        return self.__module

    def __hash__(self):
        return hash(self.__name)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented

        return self.__name == other.__name