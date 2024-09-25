#

import json
import os
import re
import subprocess
import copy
import sys
import graphlib
import antlr4 as a4
from antlr4.error.ErrorListener import ErrorListener
# TODO install this package
sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))
import parse_tree as ast  # noqa: E402
import IDLParser as pr  # noqa: E402
import IDLLexer as lx  # noqa: E402


class MyErrorListener(ErrorListener):
    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        s = '{}:{}: syntax ERROR, {}'.format(line, column, msg)
        raise Exception(s)


class IdlProcessor():

    def __init__(self, incdirs):
        self._DEFN_SPEC = {
            'modules': [],
            'structs': [],
            'consts': [],
            'typedefs': [],
            'unions': [],
            'enums': [],
            'annotations': []
        }
        self._TYPE_SPEC = {
            'name': None,
            'fqtn': None,
            'package': None,
            'is_primitive': False,
            'is_enum': False,
            'is_const': False,
            'is_struct': False,
            'is_typedef': False,
            'is_string': False,
            'is_sequence': False,
            'is_union': False,
            'user_defined': False,
            'length': None
        }
        self._DECL_SPEC = {
            'name': None,
            'is_array': False,
            'length': [],
            'optional': False
        }
        self._PRIMITIVES = [
            'floating_pt_type',
            'integer_type',
            'char_type',
            'wide_char_type',
            'boolean_type',
            'octet_type'
        ]
        self._STRINGS = [
            'string_type',
            'wide_string_type'
        ]
        if incdirs is not None:
            self._incdirs = incdirs
        else:
            self._incdirs = []
        self._source_files = []

    def currentSourceFile(self):
        if len(self._source_files) > 0:
            return self._source_files[-1]
        return None

    def pushSourceFile(self, fn):
        self._source_files.append(fn)

    def popSourceFile(self):
        del self._source_files[-1]

    def __processScopedName(self, tree):
        out = copy.deepcopy(self._TYPE_SPEC)
        out['user_defined'] = True
        parts = []
        for el in tree:
            if 'simple_declarator' in el:
                tmp = self.__processSimpleDeclarator(el['simple_declarator'])
                parts.append(tmp)
            else:
                s = 'Unknown entry in scoped name: {}'.format(tree)
                raise Exception(s)
        if len(parts) > 1:
            out['fqtn'] = '.'.join(parts)
            out['name'] = parts[-1]
        elif len(parts) == 1:
            out['fqtn'] = parts[0]
            out['name'] = parts[0]
        else:
            s = 'Scoped name did not contain valid data: {}'.format(tree)
            raise Exception(s)
        return out

    def __processPrimitiveTypeSpec(self, tree):
        out = copy.deepcopy(self._TYPE_SPEC)
        if (len(tree)) != 1:
            s = 'Unexpected tree length ({}) from {}'.format(len(tree), tree)
            raise Exception(s)
        for key, val in tree[0].items():
            names = []
            for prim in self._PRIMITIVES:
                if key == prim:
                    for ent in val:
                        names.append(ent['__payload__'])
                    break
            if not names:
                s = 'Unknown primitive type spec for {}'.format(tree)
                raise Exception(s)
            if len(names) == 1:
                out['fqtn'] = names[0]
            elif len(names) > 1:
                out['fqtn'] = ' '.join(names)
            else:
                raise Exception('No typename found for {}'.format(tree))
        out['name'] = out['fqtn']
        out['fqtn'] = out['fqtn']
        out['is_primitive'] = True
        return out

    def __processStringType(self, tree):
        out = copy.deepcopy(self._TYPE_SPEC)
        out['is_string'] = True
        out['is_primitive'] = True
        out['length'] = None
        for el in tree:
            if '__parent__' in el and el['__parent__'] in self._STRINGS:
                out['name'] = el['__payload__']
            elif 'positive_int_const' in el:
                pic = self.__processPositiveIntConst(el['positive_int_const'])
                if len(pic) > 1:
                    s = 'Unexpected str length received: {}'.format(len(pic))
                    raise Exception(s)
                out['length'] = pic[0]
            else:
                raise Exception('No typename found for {}'.format(tree))
        return out

    def __processLiteral(self, tree):
        if (len(tree)) != 1:
            s = 'Unexpected tree length ({}) from {}'.format(len(tree), tree)
            raise Exception(s)
        if '__payload__' not in tree[0]:
            s = 'Unexpected literal format: {}'.format(tree)
            raise Exception(s)
        lit = tree[0]['__payload__']
        # this isn't the best way to do this
        if lit.count('.') == 1:
            val = float(lit)
        elif lit.upper() == 'FALSE':
            val = False
        elif lit.upper() == 'TRUE':
            val = True
        elif 'E' in lit.upper():
            try:
                val = float(lit)
            except ValueError:
                val = lit.replace('"', '')
        else:
            try:
                val = int(lit)
            except ValueError:
                val = lit.replace('"', '')
        return val

    def __processTemplateTypeSpec(self, tree):
        if (len(tree)) != 1:
            s = 'Unexpected tree length ({}) from {}'.format(len(tree), tree)
            raise Exception(s)
        out = copy.deepcopy(self._TYPE_SPEC)
        for el in tree:
            tmp = {}
            if '__payload__' in el and el['__payload__'] == 'sequence':
                pass
            elif 'sequence_type' in el:
                tmp = self.__processSequenceType(el['sequence_type'])
            elif 'string_type' in el:
                tmp = self.__processStringType(el['string_type'])
            elif 'wide_string_type' in el:
                tmp = self.__processStringType(el['wide_string_type'])
            elif 'fixed_pt_type' in el:
                s = 'Unsupported fixed point type in {}'.format(tree)
                raise Exception(s)
            else:
                s = 'Unknown key el tree: {}'.format(tree)
                raise Exception(s)
            for key, val in tmp.items():
                out[key] = val
        return out

    def __processSimpleTypeSpec(self, tree):
        if (len(tree)) != 1:
            s = 'Unexpected tree length ({}) from {}'.format(len(tree), tree)
            raise Exception(s)
        out = copy.deepcopy(self._TYPE_SPEC)
        for el in tree:
            tmp = {}
            if 'template_type_spec' in el:
                tmp = self.__processTemplateTypeSpec(el['template_type_spec'])
            elif 'primitive_type_spec' in el:
                e = el['primitive_type_spec']
                tmp = self.__processPrimitiveTypeSpec(e)
            elif 'scoped_name' in el:
                tmp = self.__processScopedName(el['scoped_name'])
            else:
                s = 'Unknown entry in simple_type_spec: {}'.format(tree)
                raise Exception(s)
            for key, val in tmp.items():
                out[key] = val
        return out

    def __processConstrTypeSpec(self, tree):
        if (len(tree)) != 1:
            s = 'Unexpected tree length ({}) from {}'.format(len(tree), tree)
            raise Exception(s)
        out = copy.deepcopy(self._TYPE_SPEC)
        out = copy.deepcopy(self._TYPE_SPEC)
        for el in tree:
            tmp = {}
            if 'template_type_spec' in el:
                tmp = self.__processTemplateTypeSpec(el['template_type_spec'])
            elif 'primitive_type_spec' in el:
                e = el['primitive_type_spec']
                tmp = self.__processPrimitiveTypeSpec(e)
            elif 'scoped_name' in el:
                tmp = self.__processScopedName(el['scoped_name'])
            else:
                s = 'Unknown entry in simple_type_spec: {}'.format(tree)
                raise Exception(s)
            for key, val in tmp.items():
                out[key] = val
        out['user_defined'] = True
        return out

    def __processPrimaryExpr(self, tree):
        out = {
            'value': None
        }
        for el in tree:
            if 'literal' in el:
                tmp = self.__processLiteral(el['literal'])
                out['value'] = tmp
            elif 'scoped_name' in el:
                tmp = self.__processScopedName(el['scoped_name'])
                out['value'] = tmp['name']
            elif 'const_exp' in el:
                tmp = self.__processConstExp(el['const_exp'])
                out['value'] = tmp
            else:
                s = 'Unknown key in primary expr: {}'.format(tree)
                raise Exception(s)
        if out['value'] is None:
            s = 'Did not findvalue in: {}'.format(tree)
            raise Exception(s)
        return out

    def __processUnaryOperator(self, tree):
        if (len(tree)) > 1:
            s = 'Unexpected tree length ({}) from {}'.format(len(tree), tree)
            raise Exception(s)
        for el in tree:
            if '__payload__' in el:
                return el['__payload__']
        s = 'Malformed unary operator: {}'.format(tree)
        raise Exception(s)

    def __processUnaryExpr(self, tree):
        value = None
        operator = None
        for el in tree:
            if 'unary_operator' in el:
                operator = self.__processUnaryOperator(el['unary_operator'])
            elif 'primary_expr' in el:
                value = self.__processPrimaryExpr(el['primary_expr'])
            else:
                s = 'Unknown field in const expression. {}'. format(tree)
                raise Exception(s)
        value = value['value']
        if value is None:
            s = 'Value in literal not found in {}'.format(tree)
            raise Exception(s)
        if not operator:
            pass
        elif operator == '-':
            value = -1*value
        elif operator == '~':
            s = 'Unsure what to do w/ ~ in {}'.format(tree)
            raise Exception(s)
        elif operator == '+':
            s = 'Unsure what to do w/ ~ in {}'.format(tree)
            raise Exception(s)
        else:
            s = 'Unexpected unary expression {} in {}'.format(operator, tree)
            raise Exception(s)
        out = {
            'value': value
        }
        return out

    def __processConstExp(self, tree):
        value = None
        for el in tree:
            if 'unary_expr' in el:
                tmp = self.__processUnaryExpr(el['unary_expr'])
                value = tmp['value']
            elif 'or_expr' in el:
                s = 'Received unsupported or_expr in {}'.format(tree)
                raise Exception(s)
            else:
                s = 'Unknown field in const expression. {}'. format(tree)
                raise Exception(s)
        return value

    def __processPositiveIntConst(self, tree):
        if (len(tree)) != 1:
            s = 'Unexpected tree length ({}) from {}'.format(len(tree), tree)
            raise Exception(s)
        out = []
        for el in tree:
            if 'const_exp' in el:
                tmp = self.__processConstExp(el['const_exp'])
                out.append(tmp)
            else:
                s = 'Unknown field in const expression. {}'. format(tree)
                raise Exception(s)
        return out

    def __processSequenceType(self, tree):
        out = copy.deepcopy(self._TYPE_SPEC)
        for el in tree:
            if '__payload__' in el:
                pass
            elif 'simple_type_spec' in el:
                tmp = self.__processSimpleTypeSpec(el['simple_type_spec'])
                for key, val in tmp.items():
                    out[key] = val
            elif 'positive_int_const' in el:
                tmp = self.__processPositiveIntConst(el['positive_int_const'])
                out['length'] = tmp
            else:
                raise Exception('Unknown specifier for node {}'.format(el))
        out['is_sequence'] = True
        return out

    # TODO -- finish
    def __processTypeSpec(self, tree):
        out = copy.deepcopy(self._TYPE_SPEC)
        if (len(tree)) > 1:
            s = 'Unexpected tree length ({}) from {}'.format(len(tree), tree)
            raise Exception(s)
        for el in tree:
            if 'simple_type_spec' in el:
                tmp = self.__processSimpleTypeSpec(el['simple_type_spec'])
                for key, val in tmp.items():
                    out[key] = val
            elif 'constr_type_spec' in el:
                tmp = self.__processConstrTypeSpec(el['constr_type_spec'])
                for key, val in tmp.items():
                    out[key] = val
            else:
                s = 'Unknown type_spec for {}'.format(el)
                raise Exception(s)
        return out

    def __processArrayDeclarator(self, tree):
        out = copy.deepcopy(self._DECL_SPEC)
        for el in tree:
            if 'simple_declarator' in el:
                tmp = self.__processSimpleDeclarator(el['simple_declarator'])
                out['name'] = tmp
            elif 'fixed_array_size' in el:
                tmp = self.__processFixedArraySize(el['fixed_array_size'])
                for ll in tmp:
                    out['length'].append(ll)
            else:
                s = 'Unknown key in {}'.format(tree)
                raise Exception(s)
        return out

    def __processFixedArraySize(self, tree):
        out = []
        for el in tree:
            if 'positive_int_const' in el:
                tmp = self.__processPositiveIntConst(el['positive_int_const'])
                for en in tmp:
                    out.append(en)
        if not out:
            s = 'Fixed array size with no entries: {}'.format(tree)
            raise Exception(s)
        return out

    def __processSimpleDeclarator(self, tree):
        if (len(tree)) != 1:
            s = 'Unexpected tree length ({}) from {}'.format(len(tree), tree)
            raise Exception(s)
        out = []
        for el in tree:
            if '__payload__' in el:
                out.append(el['__payload__'])
        if not out:
            s = 'Simple declarator with no entries: {}'.format(tree)
            raise Exception(s)
        out = ' '.join(out)
        return out

    def __processDeclarator(self, tree):
        out = copy.deepcopy(self._DECL_SPEC)
        for el in tree:
            if 'simple_declarator' in el:
                tmp = self.__processSimpleDeclarator(el['simple_declarator'])
                out['name'] = tmp
            elif 'array_declarator' in el:
                tmp = self.__processArrayDeclarator(el['array_declarator'])
                out['name'] = tmp['name']
                out['length'] += tmp['length']
                out['is_array'] = True
            else:
                s = 'Unknown declarator in {}'.format(tree)
                raise Exception(s)
        return out

    def __processDeclarators(self, tree):
        out = copy.deepcopy(self._DECL_SPEC)
        for el in tree:
            if 'declarator' in el:
                tmp = self.__processDeclarator(el['declarator'])
                for key, val in tmp.items():
                    out[key] = val
            else:
                s = 'Unknown declarator in {}'.format(tree)
                raise Exception(s)
        return out

    def __processAnnotation(self, tree):
        out = []
        for el in tree:
            if 'simple_declarator' in el:
                tmp = self.__processSimpleDeclarator(el['simple_declarator'])
                out.append(tmp)
            else:
                s = 'Unknown tag in annotation: {}'.format(tree)
                raise Exception(s)

        d = {}
        d['type'] = 'annotation'
        d['payload'] = out
        return d

    def __processMember(self, tree):
        out = {
            'decl': copy.deepcopy(self._DECL_SPEC),
            'type': copy.deepcopy(self._TYPE_SPEC)
        }
        for el in tree:
            if 'type_spec' in el:
                out['type'] = self.__processTypeSpec(el['type_spec'])
            elif 'declarators' in el:
                tmp = self.__processDeclarators(el['declarators'])
                tmp['optional'] = out['decl']['optional']
                out['decl'] = tmp
            elif 'annotation' in el:
                annotations = self.__processAnnotation(el['annotation'])
                for ann in annotations['payload']:
                    if ann == 'optional':
                        out['decl']['optional'] = True
            else:
                s = 'Unknown node: {}'.format(tree)
                raise Exception(s)
        return out

    def __processElementSpec(self, tree):
        out = {
            'decl': copy.deepcopy(self._DECL_SPEC),
            'type': copy.deepcopy(self._TYPE_SPEC)
        }
        for el in tree:
            if 'type_spec' in el:
                out['type'] = self.__processTypeSpec(el['type_spec'])
            elif 'declarator' in el:
                tmp = self.__processDeclarator(el['declarator'])
                tmp2 = copy.deepcopy(self._DECL_SPEC)
                for key, val in tmp.items():
                    tmp2[key] = val
                tmp2['optional'] = out['decl']['optional']
                out['decl'] = tmp2
            elif 'annotation' in el:
                annotations = self.__processAnnotation(el['annotation'])
                for ann in annotations['payload']:
                    if ann == 'optional':
                        out['decl']['optional'] = True
            else:
                s = 'Unknown node: {}'.format(tree)
                raise Exception(s)
        return out

    def __processCaseLabel(self, tree):
        out = None
        for el in tree:
            if '__payload__' in el and el['__payload__'] == 'default':
                out = 'default'
            elif '__payload__' in el:
                pass
            elif 'const_exp' in el:
                out = self.__processConstExp(el['const_exp'])
            else:
                s = 'Unknown node: {}'.format(el)
                raise Exception(s)
        return out

    def __processCaseStmt(self, tree):
        out = {
            'decl': copy.deepcopy(self._DECL_SPEC),
            'type': copy.deepcopy(self._TYPE_SPEC),
            'discriminator': None
        }
        for el in tree:
            if 'element_spec' in el:
                tmp = self.__processElementSpec(el['element_spec'])
                out['decl'] = tmp['decl']
                out['type'] = tmp['type']
            elif 'case_label' in el:
                tmp = self.__processCaseLabel(el['case_label'])
                out['discriminator'] = tmp
            else:
                s = 'Unknown node: {}'.format(el)
                raise Exception(s)
        return out

    def __processMemberList(self, tree):
        out = []
        for el in tree:
            if 'member' in el:
                tmp = self.__processMember(el['member'])
                out.append(tmp)
            else:
                s = 'Unexpected key in: {}'.format(tree)
                raise Exception(s)
        if not out:
            s = 'Member list with no entries: {}'.format(tree)
            raise Exception(s)
        return out

    def __processSwitchBody(self, tree):
        out = []
        for el in tree:
            if 'case_stmt' in el:
                tmp = self.__processCaseStmt(el['case_stmt'])
                out.append(tmp)
            else:
                s = 'Unexpected key in: {}'.format(tree)
                raise Exception(s)
        if not out:
            s = 'Case Statement list with no entries: {}'.format(tree)
            raise Exception(s)
        return out

    def __processEnumerator(self, tree):
        out = {
            'name': None,
            'value': None
        }
        for el in tree:
            if 'simple_declarator' in el:
                tmp = self.__processSimpleDeclarator(el['simple_declarator'])
                out['name'] = tmp
            elif '__payload__' in el:
                out['value'] = int(el['__payload__'])
        return out

    def __processEnumeratorList(self, tree):
        out = []
        for el in tree:
            tmp = self.__processEnumerator(el['enumerator'])
            out.append(tmp)
        if not out:
            s = 'Member list with no entries: {}'.format(tree)
            raise Exception(s)
        return out

    def __processEnumType(self, tree):
        payload = {
            'name': None,
            'fqtn': None,
            'package': None,
            'enumerators': [],
            'directives': []
        }
        for el in tree:
            if '__payload__' in el and el['__payload__'] == 'enum':
                pass
            elif 'simple_declarator' in el:
                tmp = self.__processSimpleDeclarator(el['simple_declarator'])
                payload['name'] = tmp
            elif 'enumerator_list' in el:
                tmp = self.__processEnumeratorList(el['enumerator_list'])
                payload['enumerators'] = tmp
            else:
                s = 'Unknown tag in struct: {}'.format(el)
                raise Exception(s)
        out = {
            'type': 'enum',
            'payload': payload
        }
        return out

    def __processStructType(self, tree):
        payload = {
            'name': None,
            'members': []
        }
        for el in tree:
            if '__payload__' in el and el['__payload__'] == 'struct':
                pass
            elif 'simple_declarator' in el:
                tmp = self.__processSimpleDeclarator(el['simple_declarator'])
                payload['name'] = tmp
            elif 'member_list' in el:
                tmp = self.__processMemberList(el['member_list'])
                payload['members'] = tmp
            elif '__payload__' in el and el['__payload__'] == ':':
                pass
            elif 'scoped_name' in el:
                tmp = self.__processScopedName(el['scoped_name'])
                payload['base_class'] = tmp
            else:
                s = 'Unknown tag in struct: {}'.format(tree)
                raise Exception(s)
        out = {
            'type': 'struct',
            'payload': payload
        }
        return out

    def __processTypedefType(self, tree):
        out = {
            'decl': copy.deepcopy(self._DECL_SPEC),
            'type': copy.deepcopy(self._TYPE_SPEC)
        }
        for el in tree:
            if '__payload__' in el and el['__payload__'] == 'typedef':
                pass
            elif 'type_spec' in el:
                tmp = self.__processTypeSpec(el['type_spec'])
                out['type'] = tmp
            elif 'declarators' in el:
                tmp = self.__processDeclarators(el['declarators'])
                out['decl'] = tmp
            else:
                s = 'Unknown key in typedef: {}'.format(tree)
                raise Exception(s)
        d = {
            'type': 'typedef',
            'payload': out
        }
        return d

    def __processIntegerType(self, tree):
        out = copy.deepcopy(self._TYPE_SPEC)
        for el in tree:
            if '__payload__' in el:
                out['name'] = el['__payload__']
                out['fqtn'] = el['__payload__']
                out['is_primitive'] = True
            else:
                s = 'Unknown key in integer type: {}'.format(tree)
                raise Exception(s)
        return out

    def __processSwitchTypeSpec(self, tree):
        out = None
        for el in tree:
            if 'scoped_name' in el:
                out = self.__processScopedName(el['scoped_name'])
                out['is_enum'] = True  # Are there other option?
            elif 'integer_type' in el:
                out = self.__processIntegerType(el['integer_type'])
            else:
                pass
        return out

    def __processUnionType(self, tree):
        payload = {
            'name': None,
            'members': [],
            'discriminator': {
                'type': copy.deepcopy(self._TYPE_SPEC)
            }
        }
        for el in tree:
            if '__payload__' in el and el['__payload__'] == 'union':
                pass
            elif '__payload__' in el and el['__payload__'] == 'switch':
                pass
            elif '__payload__' in el and el['__payload__'] == '(':
                pass
            elif '__payload__' in el and el['__payload__'] == ')':
                pass
            elif 'switch_type_spec' in el:
                tmp = self.__processSwitchTypeSpec(el['switch_type_spec'])
                payload['discriminator']['type'] = tmp
            elif 'simple_declarator' in el:
                tmp = self.__processSimpleDeclarator(el['simple_declarator'])
                payload['name'] = tmp
            elif 'switch_body' in el:
                tmp = self.__processSwitchBody(el['switch_body'])
                payload['members'] = tmp
            else:
                s = 'Unknown tag in union: {}'.format(tree)
                raise Exception(s)
        out = {
            'type': 'union',
            'payload': payload
        }
        return out

    def __processConstType(self, tree):
        if (len(tree)) > 1:
            s = 'Unexpected tree length ({}) from {}'.format(len(tree), tree)
            raise Exception(s)
        out = {
            'type': None
        }
        for el in tree:
            if 'primitive_type_spec' in el:
                e = el['primitive_type_spec']
                tmp = self.__processPrimitiveTypeSpec(e)
                out['type'] = tmp
            elif 'string_type' in el:
                tmp = self.__processStringType(el['string_type'])
                out['type'] = tmp
            elif 'wide_string_type' in el:
                tmp = self.__processStringType(el['wide_string_type'])
                out['type'] = tmp
            elif 'scoped_name' in el:
                tmp = self.__processScopedName(el['scoped_name'])
                out['type'] = tmp
            elif 'fixed_pt_const_type' in el:
                s = 'Unhandled type fixed_pt_const_type in: {}'.format(tree)
                raise Exception(s)
            else:
                s = 'Unknown key in const: {}'.format(tree)
                raise Exception(s)
        return out

    def __processConstDecl(self, tree):
        out = {
            'decl': copy.deepcopy(self._DECL_SPEC),
            'type': copy.deepcopy(self._TYPE_SPEC),
            'value': None
        }
        for el in tree:
            if '__payload__' in el and el['__payload__'] == 'const':
                pass
            elif 'const_type' in el:
                tmp = self.__processConstType(el['const_type'])
                out['type'] = tmp['type']
            elif 'simple_declarator' in el:
                tmp = self.__processSimpleDeclarator(el['simple_declarator'])
                out['decl']['name'] = tmp
            elif 'const_exp' in el:
                tmp = self.__processConstExp(el['const_exp'])
                out['value'] = tmp
            else:
                s = 'Unknown key in const: {}'.format(tree)
                raise Exception(s)
        d = {}
        d['type'] = 'const'
        d['payload'] = out
        return d

    def __appendToDict(self, tmp, out):
        if tmp['type'] == 'module':
            out['modules'].append(tmp['payload'])
        elif tmp['type'] == 'const':
            out['consts'].append(tmp['payload'])
        elif tmp['type'] == 'typedef':
            out['typedefs'].append(tmp['payload'])
        elif tmp['type'] == 'union':
            out['unions'].append(tmp['payload'])
        elif tmp['type'] == 'enum':
            out['enums'].append(tmp['payload'])
        elif tmp['type'] == 'struct':
            out['structs'].append(tmp['payload'])
        elif tmp['type'] == 'annotation':
            if isinstance(tmp['payload'], list):
                for ent in tmp['payload']:
                    out['annotations'].append(ent)
            else:
                out['annotations'].append(tmp['payload'])
        else:
            s = 'Unknown type ({}) in {}'.format(tmp['type'], tmp)
            raise Exception(s)
        return out

    def __processModule(self, tree):
        out = copy.deepcopy(self._DEFN_SPEC)
        for el in tree:
            if '__payload__' in el and el['__payload__'] == 'module':
                pass
            elif 'simple_declarator' in el:
                tmp = self.__processSimpleDeclarator(el['simple_declarator'])
                out['name'] = tmp
            elif 'definition' in el:
                tmp = self.__processDefinition(el['definition'])
                out = self.__appendToDict(tmp, out)
            else:
                s = 'Unexpected tag received in {}'.format(tree)
                raise Exception(s)
        d = {}
        d['type'] = 'module'
        d['payload'] = out
        return d

    def __processDefinition(self, tree):
        if (len(tree)) != 1:
            s = 'Unexpected tree length ({}) from {}'.format(len(tree), tree)
            raise Exception(s)
        out = {
            'type': None,
            'payload': None
        }
        for el in tree:
            if 'typedef_type' in el:
                out = self.__processTypedefType(el['typedef_type'])
            elif 'struct_type' in el:
                out = self.__processStructType(el['struct_type'])
            elif 'union_type' in el:
                out = self.__processUnionType(el['union_type'])
            elif 'enum_type' in el:
                out = self.__processEnumType(el['enum_type'])
            elif 'const_decl' in el:
                out = self.__processConstDecl(el['const_decl'])
            elif 'module' in el:
                out = self.__processModule(el['module'])
            elif 'annotation' in el:
                out = self.__processAnnotation(el['annotation'])
            else:
                # there are others we don't currently support (see the grammar)
                s = 'Unexpected key in definition {}'.format(el)
                raise Exception(s)
        return out

    def __processSpecification(self, tree, out):
        for el, val in tree.items():
            if el == 'definition':
                tmp = self.__processDefinition(val)
                out = self.__appendToDict(tmp, out)
        return out

    def __flatten(self, tree):
        out = copy.deepcopy(self._DEFN_SPEC)
        for spec in tree.get('specification', []):
            out = self.__processSpecification(spec, out)
        return out

    def __traverse(self, tree, mapp):
        """
        see: https://github.com/antlr/antlr4/blob/98dc2c0f0249a67b797b151da3adf4ffbc1fd6a1/runtime/Python2/src/antlr4/ParserRuleContext.py # noqa: E501
        see: https://github.com/antlr/antlr4/blob/98dc2c0f0249a67b797b151da3adf4ffbc1fd6a1/runtime/Python2/src/antlr4/tree/Tree.py # noqa: E501
        """
        if isinstance(tree, a4.tree.Tree.TerminalNodeImpl):
            ignored = ['}', '{', ';', '=', ',', '<', '>', '@', '[', ']', '::']
            token = tree.getSymbol()
            if token.text in ignored:
                return mapp
            # tp = token.type
            nm = token.text
            pn = type(tree.getParent()).__name__
            parent = pn.lower().replace('context', '')
            mapp['__payload__'] = nm
            mapp['__parent__'] = parent
        else:
            nm = type(tree).__name__.lower().replace('context', '')
            children = []
            for el in tree.getChildren():
                nested = {}
                nested = self.__traverse(el, nested)
                if nested != {}:
                    children.append(nested)
            mapp[nm] = children
        return mapp

    def __parseAndLex(self, contents):
        try:
            istr = a4.InputStream(contents)
            lexer = lx.IDLLexer(istr)
            stream = a4.CommonTokenStream(lexer)
        except Exception as e:
            raise e
        parser = pr.IDLParser(stream)
        parser._listeners = [MyErrorListener()]
        tree = parser.specification()
        mapp = self.__traverse(tree, {})
        mapp = self.__flatten(mapp)
        return mapp

    def __preprocessFile(self, fname):

        # https://gcc.gnu.org/onlinedocs/cpp/Preprocessor-Output.html
        args = ['/usr/bin/cpp', '-E', '-C']
        for d in self._incdirs:
            args.append('-I')
            args.append(d)
        args.append(fname)

        out = ''
        try:
            out = subprocess.check_output(args).decode('UTF-8')
        except subprocess.CalledProcessError as e:
            s = 'Error: could not process {}.\n'.format(fname)
            s += '\t {}'.format(e.output)
            raise Exception(s)
        reg = re.compile(r'#\s[0-9]+\s"(.*)"([\s123-4]*)')

        rawdata = {}
        files = []
        curfile = None
        cmdln_returned = False
        for el in out.splitlines():
            if '"<command-line>" 2' in el:
                cmdln_returned = True
                continue
            if not cmdln_returned:
                continue
            m = reg.match(el)
            if m:
                curfile = m.group(1)
                mode = m.group(2)
                if mode == '1':
                    # new file
                    files.append(curfile)
                elif mode == '2':
                    # returned to a file
                    files.pop()
                    curfile = files[-1]
            elif curfile is not None:
                if curfile not in rawdata:
                    rawdata[curfile] = []
                rawdata[curfile].append(el)
            else:
                # error
                s = 'ERROR current file is not set'
                raise Exception(s)
        for key, val in rawdata.items():
            rawdata[key] = '\n'.join(val)

        # print('Parsed contents:')
        # for key, val in rawdata.items():
        #     if key == fname:
        #         continue
        #     print('--------------------------------------------------------')
        #     print('Processing included file: {}'.format(key))
        #     print(val)
        #     print('--------------------------------------------------------')
        # print('--------------------------------------------------------')
        # print('Processing primary file: {}'.format(fname))
        # print(rawdata[fname])
        # print('--------------------------------------------------------')

        return rawdata

    def __generateAst(self, tree):
        self.pushSourceFile(tree['filename'])
        root = ast.Root(tree['name'], tree['filename'])

        def processInclude(tree, parent):
            self.pushSourceFile(tree['filename'])
            pkg = None
            for d in self._incdirs:
                fp = os.path.join(d, tree['filename'])
                if os.path.exists(fp):
                    dn = os.path.dirname(fp)
                    pkg = dn.split(os.path.sep)[-1]
                    break
            if pkg is not None:
                root = ast.Root(tree['name'], tree['filename'], package=pkg)
            else:
                root = ast.Root(tree['name'], tree['filename'])
            # TODO -- should we recurse into included includes?
            for el in tree['tree']['modules']:
                tmp = processModule(el, root)
                root.addModule(tmp)
            for el in tree['tree']['structs']:
                tmp = processStruct(el, root)
                root.addStruct(tmp)
            for el in tree['tree']['enums']:
                tmp = processEnum(el, root)
                root.addEnum(tmp)
            for el in tree['tree']['consts']:
                tmp = processConst(el, root)
                root.addConst(tmp)
            for el in tree['tree']['typedefs']:
                tmp = processTypedef(el, root)
                root.addTypedef(tmp)
            for el in tree['tree']['unions']:
                tmp = processUnion(el, root)
                root.addUnion(tmp)
            fn = os.path.split(tree['filename'])[-1]
            node = ast.Include(parent, fn, root)
            self.popSourceFile()
            return node

        def processModule(tree, parent):
            node = ast.Module(parent, tree['name'])
            for el in tree['annotations']:
                tmp = processAnnotation(el, node)
                node.addSubdirective(tmp)
            for el in tree['modules']:
                tmp = processModule(el, node)
                node.addModule(tmp)
            for el in tree['structs']:
                tmp = processStruct(el, node)
                node.addStruct(tmp)
            for el in tree['enums']:
                tmp = processEnum(el, node)
                node.addEnum(tmp)
            for el in tree['consts']:
                tmp = processConst(el, node)
                node.addConst(tmp)
            for el in tree['typedefs']:
                tmp = processTypedef(el, node)
                node.addTypedef(tmp)
            for el in tree['unions']:
                tmp = processUnion(el, node)
                node.addUnion(tmp)
            return node

        def processStruct(tree, parent):
            # TODO@JML -- directives need to be enabled for members, enums, etc
            func = getattr(parent, 'subdirectives', None)
            sf = self.currentSourceFile()
            if callable(func):
                subd = func()
                node = ast.Struct(
                    parent, tree['name'], directives=subd, source_file=sf
                )
            else:
                node = ast.Struct(parent, tree['name'], source_file=sf)
            for el in tree['members']:
                tmp = processMember(el, node)
                node.addMember(tmp)
            return node

        def processEnum(tree, parent):
            sf = self.currentSourceFile()
            node = ast.Enumeration(parent, tree['name'], source_file=sf)
            for el in tree['enumerators']:
                tmp = processEnumerator(el, node)
                node.addEnumerator(tmp)
            return node

        def processMember(tree, parent):
            nm = tree['decl']['name']
            opt = tree['decl']['optional']
            tp = getType(tree)
            node = ast.Member(parent, nm, tp, opt)
            return node

        def processUnionMember(tree, parent):
            nm = tree['decl']['name']
            discriminator = tree['discriminator']
            tp = getType(tree)
            node = ast.UnionMember(parent, nm, tp, discriminator)
            return node

        def processEnumerator(tree, parent):
            val = None
            if tree['value']:
                val = tree['value']
            elif parent.enumerators():
                ens = parent.enumerators()
                if ens[-1].value() is not None:
                    val = ens[-1].value() + 1
                else:
                    n = parent.asdict()
                    s = 'Enumerator value not set in parent {}'.format(n)
                    raise Exception(s)
            else:
                val = 0
            node = ast.Enumerator(parent, tree['name'], val)
            return node

        def processTypedef(tree, parent):
            nm = tree['decl']['name']
            tp = getType(tree)
            sf = self.currentSourceFile()
            node = ast.Typedef(parent, nm, tp, source_file=sf)
            return node

        def processAnnotation(tree, parent):
            nm = tree
            node = ast.Directive(parent, nm)
            return node

        def processConst(tree, parent):
            nm = tree['decl']['name']
            val = tree['value']
            tp = getType(tree)
            sf = self.currentSourceFile()
            node = ast.Constant(parent, nm, tp, val, source_file=sf)
            return node

        def processUnion(tree, parent):
            dt = ast.SimpleType(tree['discriminator']['type']['name'])
            discrim = ast.Discriminator(dt)
            sf = self.currentSourceFile()
            node = ast.Union(
                parent, tree['name'], discrim, source_file=sf
            )
            for el in tree['members']:
                tmp = processUnionMember(el, node)
                node.addMember(tmp)
            return node

        def getType(tree):
            nm = tree['type']['name']
            if tree['decl']['is_array']:
                return ast.ArrayType(nm, length=tree['decl']['length'])
            elif tree['type']['is_sequence']:
                return ast.SimpleType(nm, is_sequence=True)
            return ast.SimpleType(nm)

        for el in tree['includes']:
            tmp = processInclude(el, root)
            root.addInclude(tmp)
        for el in tree['modules']:
            tmp = processModule(el, root)
            root.addModule(tmp)
        for el in tree['structs']:
            tmp = processStruct(el, root)
            root.addStruct(tmp)
        for el in tree['enums']:
            tmp = processEnum(el, root)
            root.addEnum(tmp)
        for el in tree['typedefs']:
            tmp = processTypedef(el, root)
            root.addTypedef(tmp)
        for el in tree['consts']:
            tmp = processConst(el, root)
            root.addConst(tmp)
        for el in tree['unions']:
            tmp = processUnion(el, root)
            root.addUnion(tmp)
        return root

    def __findType(self, tn, node, root):
        tp = {
            'name': None,
            'fqtn': None,
            'is_enum': False,
            'is_const': False,
            'is_typedef': False,
            'is_struct': False,
            'is_union': False
        }
        dtn = '.{}'.format(tn)
        for el in node.enums():
            if el.fqtn() == tn or el.fqtn().endswith(dtn):
                tp['name'] = el.name()
                tp['fqtn'] = el.fqtn()
                tp['is_enum'] = True
                return tp
        for el in node.consts():
            if el.fqtn() == tn or el.fqtn().endswith(dtn):
                tp['name'] = el.name()
                tp['fqtn'] = el.fqtn()
                tp['is_const'] = True
                return tp
        for el in node.typedefs():
            if el.fqtn() == tn or el.fqtn().endswith(dtn):
                tp['name'] = el.name()
                tp['fqtn'] = el.fqtn()
                tp['is_typedef'] = True
                return tp
        for el in node.structs():
            if el.fqtn() == tn or el.fqtn().endswith(dtn):
                tp['name'] = el.name()
                tp['fqtn'] = el.fqtn()
                tp['is_struct'] = True
                return tp
        for el in node.unions():
            if el.fqtn() == tn or el.fqtn().endswith(dtn):
                tp['name'] = el.name()
                tp['fqtn'] = el.fqtn()
                tp['is_union'] = True
                return tp
        for el in node.modules():
            tmp = self.__findType(tn, el, root)
            if tmp is not None:
                return tmp
        if isinstance(node, ast.Root):
            for el in node.includes():
                tmp = self.__findType(tn, el.tree(), root)
                if tmp is not None:
                    return tmp
        return None

    def __updateType(self, mem, tp):
        mem.type().setFqtn(tp['fqtn'])
        if tp['is_enum']:
            mem.type().setIsEnum()
        if tp['is_const']:
            mem.type().setIsConst()
        if tp['is_typedef']:
            mem.type().setIsTypedef()
        if tp['is_struct']:
            mem.type().setIsStruct()
        if tp['is_union']:
            mem.type().setIsUnion()

    def __processLayer(self, node, root):

        def resolveMember(mem, root):
            if mem.type().isArray():
                updated = False
                cpy = []
                for ll in mem.type().length():
                    if not isinstance(ll, str):
                        cpy.append(ll)
                        continue
                    tp = self.__findType(ll, root, root)
                    if not tp:
                        s = 'Unresolved dependency for type '
                        s += '{} in {}'.format(mem.asdict(), node.name())
                        raise Exception(s)
                    ll = tp['fqtn'].strip('.').replace('.', '::')
                    cpy.append(ll)
                    updated = True
                if updated:
                    mem.type().setLength(cpy)
            if mem.type().isPrimitive() or mem.type().isString():
                return
            nm = mem.type().name()
            tp = self.__findType(nm, root, root)
            if not tp:
                s = 'Unresolved dependency for type '
                s += '{} in {}'.format(mem.asdict(), node.name())
                raise Exception(s)
            self.__updateType(mem, tp)

        for mod in node.modules():
            self.__processLayer(mod, root)
        for el in node.structs():
            for mem in el.members():
                resolveMember(mem, root)
        for el in node.unions():
            resolveMember(el.discriminator(), root)
            for mem in el.members():
                resolveMember(mem, root)
        for el in node.consts():
            if el.type().isPrimitive() or el.type().isString():
                continue
            nm = el.type().name()
            tp = self.__findType(nm, root, root)
            if not tp:
                s = 'Unresolved dependency for type '
                s += '{} in {}'.format(el.asdict(), node.name())
                raise Exception(s)
            self.__updateType(el, tp)
        for el in node.typedefs():
            if el.type().isPrimitive() or el.type().isString():
                continue
            nm = el.type().name()
            tp = self.__findType(nm, root, root)
            if not tp:
                s = 'Unresolved dependency for type '
                s += '{} in {}'.format(el.asdict(), node.name())
                raise Exception(s)
            self.__updateType(el, tp)

    def __processAggregates(self, root):
        # the point of this method is to determine the ordering of elements
        # inside a single IDL file so they can be decalred in the correct order
        def getAllStructs(tree, structs=None):
            if structs is None:
                structs = []
            for el in tree.structs():
                structs.append(el)
            for el in tree.modules():
                structs = getAllStructs(el, structs)
            return structs

        def getAllUnions(tree, unions=None):
            if unions is None:
                unions = []
            for el in tree.unions():
                unions.append(el)
            for el in tree.modules():
                unions = getAllUnions(el, unions)
            return unions
        structs = getAllStructs(root)
        unions = getAllUnions(root)
        aggregates = {}
        for el in structs:
            aggregates[el.fqtn()] = {'type': 'struct', 'payload': el}
        for el in unions:
            aggregates[el.fqtn()] = {'type': 'union', 'payload': el}
        graph = {}
        for key, val in aggregates.items():
            if key not in graph:
                graph[key] = []
            payload = val['payload']
            for mem in payload.members():
                if not mem.type().isStruct() and not mem.type().isUnion():
                    continue
                fqtn = mem.type().fqtn()
                if fqtn not in aggregates:
                    # this is from an include file
                    continue
                graph[key].append(mem.type().fqtn())
        ts = graphlib.TopologicalSorter(graph)
        keys = tuple(ts.static_order())
        result = []
        for key in keys:
            if key in aggregates:
                d = aggregates[key]
                if d['type'] == 'union':
                    result.append(ast.Aggregate(d['payload'], is_union=True))
                elif d['type'] == 'struct':
                    result.append(ast.Aggregate(d['payload'], is_struct=True))
            else:
                raise Exception('Could not find \'{}\' in {}'.format(
                    key, self.currentSourceFile()))
        return result

    def __resolveDependencies(self, root):
        # need to resolve dependencies in modules, structs, typedefs, & consts
        # looking to see if each is referencing a user-defined type (^^^^^^^^)
        # and then determine the fqtn of each. We don't need to implement name
        # resolution in the includes but we do need to look at the includes
        self.__processLayer(root, root)
        result = self.__processAggregates(root)
        # print(json.dumps([x.asdict() for x in result], indent=4))
        root.setAggregates(result)
        return root

    def processFile(self, fname, debug=False):
        def getStemNoExtension(p):
            st = os.path.split(p)[-1].replace('.idl', '')
            return st
        rawdata = self.__preprocessFile(fname)
        tree = {}
        tree['includes'] = []
        for key, val in rawdata.items():
            if key == fname:
                continue
            f = {}
            f['name'] = getStemNoExtension(key)
            f['path'] = os.path.split(key)[0]
            f['filename'] = key
            f['tree'] = self.__parseAndLex(val)
            tree['includes'].append(f)
        tree['name'] = getStemNoExtension(fname)
        tree['path'] = os.path.split(fname)[0]
        tree['filename'] = fname
        contents = self.__parseAndLex(rawdata[fname])
        for k, v in contents.items():
            tree[k] = v
        abstree = self.__generateAst(tree)
        if debug:
            print(json.dumps(abstree.asdict(), indent=4))
        resolved = self.__resolveDependencies(abstree)
        return resolved
