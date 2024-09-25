#!/usr/bin/python3

import os
import sys
import unittest as ut
path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
sys.path.insert(1, path)
from generator import generator_functions as gf  # noqa: E402
import generator as p  # noqa: E402


class TestMethods(ut.TestCase):

    def test_one(self):
        d = [os.path.join('test_data')]
        f = os.path.join('test_data', 'test_one.idl')
        tree = p.IdlProcessor(d).processFile(f).asdict()
        cont = gf.getAllEnums(tree)
        self.assertEqual(len(cont), 2)
        cont = gf.getAllStructs(tree)
        self.assertEqual(len(cont), 1)

    def test_two(self):
        d = [os.path.join('test_data')]
        f = os.path.join('test_data', 'SomeType.idl')
        prsr = p.IdlProcessor(d)
        tree = prsr.processFile(f)
        cont = gf.getAllEnums(tree.asdict(), [])
        self.assertEqual(len(cont), 0)
        cont = gf.getAllStructs(tree.asdict(), [])
        self.assertEqual(len(cont), 1)

if __name__ == '__main__':
    ut.main()
