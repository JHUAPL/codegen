import sys
import os
import re
import json
# from pattern.text.en import singularize
from inflection import singularize
sys.path.append(os.path.abspath(os.getenv('PROJECT_PATH',
                os.path.realpath(__file__))))
# import INTERNAL_TYPES
from project_types \
    import INTERNAL_TYPES, INTERNAL_HEADERS, SERIALIZER_HEADERS  # noqa: E402

PRIMITIVE_TYPES = {
    'boolean': 'bool',
    'byte': 'unsigned char',
    'char8': 'char',
    'char16': 'std::char16_t',
    'int8': 'std::int8_t',
    'uint8': 'std::uint8_t',
    'int16': 'std::int16_t',
    'uint16': 'std::uint16_t',
    'int32': 'std::int32_t',
    'uint32': 'std::uint32_t',
    'int64': 'std::int64_t',
    'uint64': 'std::uint64_t',
    'float32': 'float',
    'float64': 'double',
    'string': 'std::string',
    'wstring': 'std::wstring',
    'char': 'char',
    'wchar': 'wchar',
    'octet': 'unsigned char',
    'short': 'std::int16_t',
    'unsigned short': 'std::uint16_t',
    'long': 'std::int32_t',
    'unsigned long': 'std::uint32_t',
    'long long': 'std::int64_t',
    'unsigned long long': 'std::uint64_t',
    'float': 'float',
    'double': 'double',
    'long double': 'long double',
}

# these shouldn't be used since the size varies by machine data model
DEPRECATED_PRIMITIVE_TYPES = {
    'unsignedShort': 'unsigned short',
    'unsignedLong': 'unsigned long',
    'longLong': 'long long',
    'unsignedLongLong': 'unsigned long long',
    'longDouble': 'long double'
}


def getLangType(el, prefix):
    if el in PRIMITIVE_TYPES:
        return PRIMITIVE_TYPES[el]
    if el in DEPRECATED_PRIMITIVE_TYPES:
        return DEPRECATED_PRIMITIVE_TYPES[el]
    if el in INTERNAL_TYPES:
        el = INTERNAL_TYPES[el]
    else:
        if el.startswith('.'):
            el = el.strip('.')
        el = '.' + prefix + '.' + el
    if el.startswith('.'):
        el = el.strip('.')
    el = el.replace('.', '::')
    return el


def removePrefix(s, prefix):
    if s.startswith(prefix):
        return s[len(prefix):]
    return s


def getType(d, prefix, optional=False):
    typename = getLangType(d['fqtn'], prefix)
    if 'is_array' in d and d['is_array']:
        for element in d['length']:
            typename = 'std::array<{}, {}>'.format(typename, element)
    if 'is_sequence' in d and d['is_sequence']:
        typename = 'std::vector<{}>'.format(typename)
    if optional:
        typename = 'std::optional<{}>'.format(typename)
    return typename


def isSequence(d):
    if 'is_sequence' in d and d['is_sequence']:
        return True
    return False


def getAppender(d):
    s = 'add{}'.format(singularize(d.capitalize()))
    return s


def printJson(d):
    print(json.dumps(d, indent=4))


def findPkgSpec(dn):
    parts = dn.split(os.path.sep)
    if len(parts) == 0:
        return None
    p = '/'.join(parts[:-1])
    fname = os.path.join(p, 'pkg_spec.json')
    if os.path.isfile(fname):
        return fname
    return findPkgSpec(p)


def getPackageName(dn):
    fname = findPkgSpec(dn)
    with open(fname, 'r') as f:
        pspec = json.load(f)
        return pspec['pkg_name']


def getInclude(inc, pkg, suffix=None):
    # this function is terrible. We need to determine whether the user wants
    # an include that looks like <file>, <pkg>/<file>, or <pkg>/<dirs>/<file>
    # independent of how they include the file in their IDL or how their IDL
    # folder structure is setup. Additionally, the files we are searching for
    # may be specified in an absolute path or relative path, which makes this
    # even more annoying
    fname = inc['name']
    if fname in INTERNAL_HEADERS:
        return INTERNAL_HEADERS[fname]
    if 'tree' in inc and inc['tree']['dirname'] is not None:
        inc = inc['tree']
    dn = inc['dirname']
    # if os.path.isabs(dn):
    smallpkg = pkg
    if smallpkg + '/' in dn:
        parts = dn.split(smallpkg)
        dn = parts[-1]
    elif os.path.isabs(dn):
        pn = getPackageName(dn)
        if pn is None:
            s = 'Could not find pkg_spec.json near {}'.format(dn)
            raise Exception(s)
        if pn not in dn:
            s = 'Could not find package {} in path {}'.format(pn, dn)
            raise Exception(s)
        dn = dn.split(pn)[1]
        pkg = pn
    temp = pkg + '/' + dn.replace('idl/', '')

    s = temp + '/' + fname
    if suffix is not None:
        s += suffix
    s += '.hpp'
    s = s.strip(os.path.sep).replace('idl/', '').replace('//', '/')
    return s


def getSerializerInclude(inc, pkg=None):
    fname = inc['name']
    if fname in SERIALIZER_HEADERS:
        s = SERIALIZER_HEADERS[fname]
        return s
    s = getInclude(inc, pkg)
    parts = s.split(os.path.sep)
    parts[-1] = 'detail'
    parts.append('{}Serializer.hpp'.format(fname))
    s = os.path.sep.join(parts)
    s = s.strip(os.path.sep)
    return s


def getInternalType(typename):
    if typename in INTERNAL_TYPES:
        return INTERNAL_TYPES[typename]
    return None


def isSpecialType(d):
    if 'type' not in d:
        if d in INTERNAL_HEADERS:
            return True
        return False
    typename = d['type']['fqtn']
    tp = getInternalType(typename)
    if tp is not None:
        return True
    return False


def getFullyQualInternalTypeName(d, prefix):
    return getLangType(d['fqtn'], prefix)


def findConst(consts, key):
    for el in consts:
        if 'fqtn' in el and 'value' in el:
            if el['fqtn'] == key:
                return el['value']
    return None


def isInt(value):
    try:
        int(value)
        return True
    except ValueError:
        return False


# These methods unroll the ast into a list of structs, enums, typedefs, ...
def getAllStructs(d, structs=None, recurse=True):
    if structs is None:
        structs = []
    if d.get('structs', None) is not None:
        for el in d['structs']:
            structs.append(el)
    if recurse and d.get('modules', None) is not None:
        for el in d['modules']:
            structs = getAllStructs(el, structs)
    return structs


def getAllEnums(d, enums=None, recurse=True):
    if enums is None:
        enums = []
    if d.get('enums', None) is not None:
        for el in d['enums']:
            enums.append(el)
    if recurse and d.get('modules', None) is not None:
        for el in d['modules']:
            enums = getAllEnums(el, enums)
    return enums


def getAllConsts(d, consts=None, recurse=True):
    if consts is None:
        consts = []
    if d.get('consts', None) is not None:
        for el in d['consts']:
            consts.append(el)
    if recurse and d.get('modules', None) is not None:
        for el in d['modules']:
            consts = getAllConsts(el, consts)
    return consts


def getUnion(d, ctx):
    unions = getAllUnions(ctx)
    for union in unions:
        if union['name'] == d['type']['name']:
            return union
    return None


def getAllUnions(d, unions=None, recurse=True):
    if unions is None:
        unions = []
    if d.get('unions', None) is not None:
        for el in d['unions']:
            unions.append(el)
    if recurse and d.get('modules', None) is not None:
        for el in d['modules']:
            unions = getAllUnions(el, unions)
    return unions


def getAllTypedefs(d, typedefs=None, recurse=True):
    if typedefs is None:
        typedefs = []
    if d.get('typedefs', None) is not None:
        for el in d['typedefs']:
            typedefs.append(el)
    if recurse and d.get('modules', None) is not None:
        for el in d['modules']:
            typedefs = getAllTypedefs(el, typedefs)
    return typedefs


def getAllIncludes(d, includes=None, recurse=True):
    if includes is None:
        includes = []
    if d.get('includes', None) is not None:
        for el in d['includes']:
            tree = el['tree']
            includes.append(tree['filename'])
            if recurse:
                includes = getAllIncludes(tree, includes)
    return includes



def getMethodNameStem(method):
    head, _ = __getHeadTail(method)
    return head[-1]


def getFullyQualMethodName(method, classname):
    head, tail = __getHeadTail(method)
    nm = ' '.join(head[:-1]) + ' ' + classname + '::' + head[-1] + '(' + tail
    return nm


def getFunctionPtrName(method, classname):
    head, _ = __getHeadTail(method)
    nm = classname + '::' + head[-1]
    return nm


def getCamelCaseName(name):
    # the input is 'pkg_name::msgType'
    nm = name.replace('::', '.').split('.')[-1]
    nm = re.sub(r'(?<!^)(?=[A-Z])', '_', nm).lower()
    return nm


def getMessageRegistrationInternal(entity):
    def __isNested(struct):
        if len(struct['directives']) > 0:
            dirs = struct['directives']
            for d in dirs:
                if d['name'] == 'nested':
                    return True
        return False

    def __extractStruct(struct):
        el = dict()
        el['name'] = struct['name']
        el['pkg'] = struct['package'].strip('.').replace('.', '::')
        return el

    def __extractModule(module):
        elements = []
        for mod in module['modules']:
            elements = elements + __extractModule(mod)
        for struct in module['structs']:
            if not __isNested(struct):
                elements.append(__extractStruct(struct))
        return elements
    data = []
    for module in entity['modules']:
        data = data + __extractModule(module)
    for struct in entity['structs']:
        if not __isNested(struct):
            data.append(__extractStruct(struct))
    return data


def __getHeadTail(method):
    parts = method.split('(')
    # the method should look like: 'return_type methodName(arg)'
    head = parts[0].split()
    tail = parts[1]
    return head, tail


def __lowerFirst(s):
    return s[:1].lower() + s[1:] if s else ''
