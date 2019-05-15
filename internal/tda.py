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


class TreeNode:
    def __init__(self, data):
        if data is None:
            raise ValueError("'data' can not be None")

        self.__data = data
        self.__children = []

    def get_data(self):
        return self.__data

    def degree(self):
        return len(self.__children)

    def is_leaf(self):
        return self.degree() == 0

    def get_children(self):
        """
        :return: List of TreeNode objects
        """
        return self.__children

    def get_child_index(self, node):
        found = False
        i = 0
        while not found and i < len(self.__children):
            if self.__children[i] is node:
                found = True
            else:
                i += 1

        return i if found else -1

    def get_child_at(self, index):
        return self.__children[index]


class Tree:
    def __init__(self, root):
        self.__root = root

    def is_empty(self):
        return self.__root is None

    def get_root(self):
        return self.__root

    def get_pre_order_node_list(self):
        node_list = []
        if not self.is_empty():
            node_list.append(self.__root)
            for node in node_list:
                if node.degree() > 0:
                    node_list.extend(node.get_children())

        return node_list

    def get_tree_level(self):
        node_list = self.get_pre_order_node_list()
        tree_level = 0
        for node in node_list:
            node_level = self.get_node_level(node)
            if node_level > tree_level:
                tree_level = node_level

        return tree_level

    def get_father(self, node):
        father = None
        if node is not self.__root:
            node_list = self.get_pre_order_node_list()
            found = False
            i = 0
            while not found and i < len(node_list):
                candidate_father = node_list[i]
                children = candidate_father.get_children()

                j = 0
                while not found and j < len(children):
                    item = children[j]
                    if item is node:
                        found = True

                    j += 1

                if found:
                    father = candidate_father

                i += 1

        return father

    def get_node_level(self, node):
        if node is self.__root:
            return 0
        else:
            return self.get_node_level(self.get_father(node)) + 1

    def get_nodes_at_level(self, level):
        founds = []
        for node in self.get_pre_order_node_list():
            if self.get_node_level(node) is level:
                founds.append(node)

        return founds

    def find_node_by_data(self, data, predicate_fn):
        for node in self.get_pre_order_node_list():
            if predicate_fn(node.get_data(), data):
                return node

        return None

    def remove_subtree(self, node):
        father = self.get_father(node)
        if father is not None:
            father.get_children().remove(node)
