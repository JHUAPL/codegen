#!/usr/bin/python3

import os
import unittest as ut
import sys
path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..')
sys.path.insert(1, path)
import generator as p  # noqa: E402

tdp = [os.path.join('test_data')]


class TestMethods(ut.TestCase):

    def test_one(self):
        # test various funcitonality
        f = os.path.join('test_data', 'test_one.idl')
        t = p.IdlProcessor(tdp).processFile(f)
        self.assertEqual(t.name(), 'test_one')
        self.assertEqual(t.structs().length(), 1)
        m = t.structs()[0].members()
        self.assertEqual(m.length(), 4)
        self.assertEqual(m[0].name(), 'one')
        self.assertEqual(m[1].name(), 'two')
        self.assertEqual(m[2].name(), 'three')
        self.assertEqual(m[3].name(), 'four')
        self.assertEqual(m[0].type().name(), 'char')
        self.assertEqual(m[1].type().name(), 'string')
        self.assertEqual(m[1].isOptional(), True)
        self.assertEqual(m[2].type().name(), 'boolean')
        self.assertEqual(m[2].isOptional(), False)
        self.assertEqual(m[3].type().name(), 'float')
        self.assertEqual(m[3].isOptional(), False)
        self.assertEqual(t.modules().length(), 1)
        self.assertEqual(t.modules()[0].name(), 'test_one')
        self.assertEqual(t.modules()[0].consts().length(), 1)
        self.assertEqual(t.modules()[0].consts()[0].name(), 'PI')
        self.assertEqual(t.modules()[0].consts()[0].type().name(), 'double')
        self.assertEqual(t.modules()[0].consts()[0].value(), 3.14)
        self.assertEqual(t.modules()[0].modules().length(), 1)
        self.assertEqual(t.modules()[0].modules()[0].consts().length(), 0)
        # self.assertEqual(t.structs()[0].directives().length(), 2)
        self.assertEqual(t.modules()[0].modules()[0].name(), 'inner')
        self.assertEqual(t.modules()[0].modules()[0].enums().length(), 2)
        self.assertEqual(
            t.modules()[0].modules()[0].enums()[0].name(), 'test_enum')
        self.assertEqual(
            t.modules()[0].modules()[0].enums()[1].name(), 'test_enum2')
        self.assertEqual(
            t.modules()[0].modules()[0].enums()[0].enumerators().length(), 1)
        self.assertEqual(
            t.modules()[0].modules()[0].enums()[1].enumerators().length(), 2)
        # self.assertEqual(
        # t.structs()[0].directives()[0].data(), ['Copy this!'])

    def test_two(self):
        # test enums
        f = os.path.join('test_data', 'test_two.idl')
        t = p.IdlProcessor(tdp).processFile(f)
        self.assertEqual(t.name(), 'test_two')
        e = t.enums()
        self.assertEqual(e.length(), 4)

        def enumTest(e, nm, enumerators):
            self.assertEqual(e.name(), nm)
            self.assertEqual(e.enumerators().length(), len(enumerators))
            for data, test in zip(e.enumerators(), enumerators):
                self.assertEqual(data.name(), test['nm'])
                self.assertEqual(data.value(), test['val'])

        enumTest(e[0], 'enum1', [
            {'nm': 'A', 'val': 1},
            {'nm': 'B', 'val': 2}])
        enumTest(e[1], 'enum2', [
            {'nm': 'A', 'val': 0},
            {'nm': 'B', 'val': 1},
            {'nm': 'C', 'val': 2}]
        )
        enumTest(e[2], 'enum3', [
            {'nm': 'A', 'val': 1},
            {'nm': 'B', 'val': 2}]
        )
        enumTest(e[3], 'enum4', [
            {'nm': 'A', 'val': 10},
            {'nm': 'B', 'val': 20}]
        )

        e = t.modules()[0].enums()
        self.assertEqual(e.length(), 3)
        enumTest(e[0], 'enum1', [
            {'nm': 'A', 'val': 1},
            {'nm': 'B', 'val': 2}]
        )
        enumTest(e[1], 'enum2', [
            {'nm': 'A', 'val': 0},
            {'nm': 'B', 'val': 1},
            {'nm': 'C', 'val': 2}]
        )
        enumTest(e[2], 'enum3', [
            {'nm': 'A', 'val': 1},
            {'nm': 'B', 'val': 2}]
        )

    def test_three(self):
        # test all the valid types
        f = os.path.join('test_data', 'test_three.idl')
        t = p.IdlProcessor(tdp).processFile(f)
        self.assertEqual(t.name(), 'test_three')
        s = t.structs()
        self.assertEqual(s.length(), 4)
        elements = [
            {'nm': 'a', 'tp': 'boolean'},
            {'nm': 'b', 'tp': 'octet'},
            {'nm': 'c', 'tp': 'char'},
            {'nm': 'd', 'tp': 'wchar'},
            {'nm': 'e', 'tp': 'int16'},
            {'nm': 'f', 'tp': 'uint16'},
            {'nm': 'g', 'tp': 'int32'},
            {'nm': 'h', 'tp': 'uint32'},
            {'nm': 'i', 'tp': 'int64'},
            {'nm': 'j', 'tp': 'uint64'},
            {'nm': 'k', 'tp': 'float'},
            {'nm': 'l', 'tp': 'double'},
            {'nm': 'm', 'tp': 'char'},
            {'nm': 'n', 'tp': 'wchar'},
            {'nm': 'o', 'tp': 'octet'},
            {'nm': 'p', 'tp': 'short'},
            {'nm': 'q', 'tp': 'unsigned short'},
            {'nm': 'r', 'tp': 'long'},
            {'nm': 's', 'tp': 'unsigned long'},
            {'nm': 't', 'tp': 'long long'},
            {'nm': 'u', 'tp': 'unsigned long long'},
            {'nm': 'v', 'tp': 'float'},
            {'nm': 'w', 'tp': 'double'},
            {'nm': 'x', 'tp': 'long double'},
            {'nm': 'y', 'tp': 'string'},
            {'nm': 'z', 'tp': 'wstring'}
        ]
        self.assertEqual(s[0].members().length(), len(elements))
        for data, test in zip(s[0].members(), elements):
            self.assertEqual(data.name(), test['nm'])
            self.assertEqual(data.type().name(), test['tp'])
            self.assertEqual(data.isOptional(), False)
        self.assertEqual(s[1].members().length(), len(elements))
        for data, test in zip(s[1].members(), elements):
            self.assertEqual(data.name(), test['nm'])
            self.assertEqual(data.type().name(), test['tp'])
            self.assertEqual(data.isOptional(), True)
        self.assertEqual(s[2].members().length(), len(elements))
        for data, test in zip(s[2].members(), elements):
            self.assertEqual(data.name(), test['nm'])
            self.assertEqual(data.type().name(), test['tp'])
            self.assertEqual(data.isOptional(), False)
        self.assertEqual(s[3].members().length(), 2)
        self.assertEqual(s[3].members()[0].name(), 'a')
        self.assertEqual(s[3].members()[0].type().name(), 's1')
        self.assertEqual(s[3].members()[0].isOptional(), True)
        self.assertEqual(s[3].members()[1].name(), 'b')
        self.assertEqual(s[3].members()[1].type().name(), 's2')
        self.assertEqual(s[3].members()[1].isOptional(), False)
        elements = [
            {'nm':  'aa', 'tp': 'boolean'},
            {'nm':  'ee', 'tp': 'int16'},
            {'nm':  'ff', 'tp': 'uint16'},
            {'nm':  'gg', 'tp': 'int32'},
            {'nm':  'hh', 'tp': 'uint32'},
            {'nm':  'ii', 'tp': 'int64'},
            {'nm':  'jj', 'tp': 'uint64'},
            {'nm':  'kk', 'tp': 'float'},
            {'nm':  'll', 'tp': 'double'},
            {'nm':  'pp', 'tp': 'short'},
            {'nm':  'qq', 'tp': 'unsigned short'},
            {'nm':  'rr', 'tp': 'long'},
            {'nm':  'ss', 'tp': 'unsigned long'},
            {'nm':  'tt', 'tp': 'long long'},
            {'nm':  'uu', 'tp': 'unsigned long long'},
            {'nm':  'vv', 'tp': 'float'},
            {'nm':  'ww', 'tp': 'double'},
            {'nm':  'xx', 'tp': 'long double'},
            {'nm':  'yy', 'tp': 'string'},
            {'nm':  'zz', 'tp': 'wstring'},
            {'nm':  'sciF', 'tp': 'float'},
            {'nm':  'sciD', 'tp': 'double'},
            {'nm':  'sciLD', 'tp': 'long double'},
        ]
        c = t.consts()
        self.assertEqual(c.length(), len(elements)+1)
        for data, test in zip(c, elements):
            self.assertEqual(data.name(), test['nm'])
            self.assertEqual(data.type().name(), test['tp'])
            FLOATS = ['double', 'float', 'float32', 'float64', 'longDouble']
            if test['tp'] in FLOATS:
                self.assertEqual(data.value(), 1.0)
            elif test['tp'] in ['string']:
                self.assertEqual(data.value(), 'aa')
            elif test['tp'] in ['wstring']:
                self.assertEqual(data.value(), 'bb')
            elif test['tp'] in ['boolean']:
                self.assertEqual(data.value(), False)
            else:
                self.assertEqual(data.value(), 1)
        self.assertEqual(c[-1].name(), 'aaa')
        self.assertEqual(c[-1].type().name(), 'boolean')
        self.assertEqual(c[-1].value(), True)

    def test_four(self):
        f = os.path.join('test_data', 'test_four.idl')
        t = p.IdlProcessor(tdp).processFile(f)
        self.assertEqual(t.name(), 'test_four')
        self.assertEqual(t.includes().length(), 3)
        self.assertEqual(t.includes()[0].name(), 'test_one')
        self.assertEqual(t.includes()[1].name(), 'test_two')
        self.assertEqual(t.includes()[2].name(), 'test_three')

    def test_five(self):
        f = os.path.join('test_data', 'test_five.idl')
        t = p.IdlProcessor(tdp).processFile(f)
        self.assertEqual(t.name(), 'test_five')
        self.assertEqual(t.structs().length(), 4)
        s = t.structs()[0]
        self.assertEqual(s.members()[0].name(), 'x')
        self.assertEqual(s.members()[0].type().name(), 'double')
        self.assertEqual(s.members()[0].type().isArray(), True)
        self.assertEqual(s.members()[0].type().length(), [3])
        s = t.structs()[1]
        self.assertEqual(s.members()[0].name(), 'sec')
        self.assertEqual(s.members()[0].type().name(), 'uint64')
        self.assertEqual(s.members()[0].type().isArray(), False)
        self.assertEqual(s.members()[1].name(), 'nsec')
        self.assertEqual(s.members()[1].type().name(), 'uint32')
        self.assertEqual(s.members()[1].type().isArray(), False)
        s = t.structs()[2]
        self.assertEqual(s.members()[0].name(), 'y')
        self.assertEqual(s.members()[0].type().name(), 'double')
        self.assertEqual(s.members()[0].type().isArray(), True)
        self.assertEqual(s.members()[0].type().length(), [3, 3])
        s = t.structs()[3]
        self.assertEqual(s.members()[0].name(), 'z')
        self.assertEqual(s.members()[0].type().name(), 'Vector3')
        self.assertEqual(s.members()[1].type().name(), 'Time')

    def test_six(self):
        f = os.path.join('test_data', 'test_six.idl')
        t = p.IdlProcessor(tdp).processFile(f)
        self.assertEqual(t.name(), 'test_six')
        self.assertEqual(t.enums().length(), 0)
        self.assertEqual(t.modules().length(), 1)
        self.assertEqual(t.modules()[0].modules().length(), 1)
        self.assertEqual(t.modules()[0].modules()[0].modules().length(), 1)
        m = t.modules()[0].modules()[0].modules()[0]
        self.assertEqual(m.enums().length(), 3)
        e = m.enums()[0]
        self.assertEqual(e.name(), 'enum1')
        self.assertEqual(e.fqtn(), '.module1.module2.module3.enum1')
        e = m.enums()[1]
        self.assertEqual(e.name(), 'enum2')
        self.assertEqual(e.fqtn(), '.module1.module2.module3.enum2')
        e = m.enums()[2]
        self.assertEqual(e.name(), 'enum3')
        self.assertEqual(e.fqtn(), '.module1.module2.module3.enum3')

    def test_seven(self):
        def will_raise():
            fn = os.path.join('test_data', 'test_seven.idl')
            p.IdlProcessor(tdp).processFile(fn)
        self.assertRaises(Exception, will_raise)

    def test_twelve(self):
        f = os.path.join('test_data', 'test_twelve.idl')
        t = p.IdlProcessor(tdp).processFile(f)
        self.assertEqual(t.name(), 'test_twelve')

    def test_thirteen(self):
        def will_raise():
            fn = os.path.join('test_data', 'circular_include_one.idl')
            p.IdlProcessor(tdp).processFile(fn)
        self.assertRaises(Exception, will_raise)

    def test_fourteen(self):
        f = os.path.join('test_data', 'test_fourteen.idl')
        t = p.IdlProcessor(tdp).processFile(f)
        self.assertEqual(t.name(), 'test_fourteen')
        self.assertEqual(t.enums().length(), 0)
        self.assertEqual(t.modules().length(), 1)
        self.assertEqual(t.modules()[0].consts().length(), 2)
        self.assertEqual(t.modules()[0].structs().length(), 4)
        c = t.modules()[0].consts()[0]
        self.assertEqual(c.name(), 'RANGE_BINS')
        self.assertEqual(c.type().name(), 'uint16')
        self.assertEqual(c.value(), 512)
        c = t.modules()[0].consts()[1]
        self.assertEqual(c.name(), 'SCANS_PER_WEDGE')
        self.assertEqual(c.type().name(), 'uint16')
        self.assertEqual(c.value(), 32)
        s = t.modules()[0].structs()[0]
        self.assertEqual(s.name(), 'ScanLine')
        m = s.members()[0]
        self.assertEqual(m.name(), 'line')
        self.assertEqual(m.type().name(), 'int32')
        self.assertEqual(m.type().length(),
                         ['perception_msgs::RANGE_BINS'])
        s = t.modules()[0].structs()[1]
        self.assertEqual(s.name(), 'RadarScanLineWedge')
        m = s.members()[0]
        self.assertEqual(m.name(), 'scans')
        self.assertEqual(m.type().name(), 'int32')
        self.assertEqual(m.type().length(), None)
        s = t.modules()[0].structs()[2]
        self.assertEqual(s.name(), 'AnotherTest')
        m = s.members()[0]
        self.assertEqual(m.name(), 'scans')
        self.assertEqual(m.type().name(), 'int32')
        self.assertEqual(m.type().length(),
                         ['perception_msgs::SCANS_PER_WEDGE'])
        s = t.modules()[0].structs()[3]
        self.assertEqual(s.name(), 'AnotherTest2')
        m = s.members()[0]
        self.assertEqual(m.name(), 'scans')
        self.assertEqual(m.type().name(), 'int32')
        self.assertEqual(m.type().length(),
                         ['perception_msgs::SCANS_PER_WEDGE', 4])


if __name__ == '__main__':
    ut.main()
