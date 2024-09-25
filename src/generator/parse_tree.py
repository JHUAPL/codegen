# AST package

# define the Abstract Syntax Tree (AST) for the parsed data types
#
# We have the following types:
#  - root / global node
#  - include declarations
#  - constant declarations
#  - typedef declarations
#  - struct declarations
#  - enumeration declarations
#  - module declarations
#
# The root node has lists of the following:
#  - includes
#  - typedefs
#  - modules
#  - structs
#  - enums
#  - constants
#
# Each node has the following:
#  - name
#  - parent (None in the case of the root node)
#
# Each include has the following:
#  - filename
#
# Each module node has the following:
#  - name
#  - typedefs
#  - modules
#  - structs
#  - enums
#  - constants
#
# Each typedef node defines the following:
#  - name
#  - underlying type
#  - dimension (arrays only)
#  - sequence length (sequences only where -1 ==> unbounded)
#
# Each constant node defines the following:
#  - name
#  - underlying type
#  - value
#
# Each enumeration node has the following:
#  - name
#  - enumerators
#
# Each structure has the following:
#  - name
#  - members
#  - consts
#
# Each member has the following:
#  - name
#  - underlying type
#  - dimension (arrays only)
#  - sequence length (sequences only where -1 ==> unbounded)
#  - optional flag
#
# Some objects can be array-like:
#  - if dimension is set, then a fixed size array is produced
#  - sequence length is ignored
#

import os
import copy


class SizedList(list):
    def length(self):
        return len(self)


class Node():
    def __init__(self, parent=None, name=None, source_file=None):
        self._parent = parent
        self._name = name
        self._source_file = source_file

    def asdict(self):
        # TODO -- should this call the parent?
        if self._parent is not None:
            return {
                'name': self._name,
                'source_file': self._source_file
            }
        return {
            'parent': None,
            'name': self._name,
            'source_file': self._source_file
        }

    def name(self):
        if self._name is not None:
            return self._name
        return 'global'

    def parent(self):
        return self._parent

    def root(self):
        if self._parent is not None:
            return self._parent.root()
        return self

    def sourceFile(self):
        return self._source_file


class Root(Node):
    def __init__(self, name, filename, package=None):
        super().__init__(parent=None, name=name)
        self._fqtn = ''
        self._filename = filename
        if package is not None:
            self._package = package
        else:
            self._package = os.path.dirname(self.filename()).split('/')[-1]
        self._includes = SizedList()
        self._modules = SizedList()
        self._structs = SizedList()
        self._typedefs = SizedList()
        self._consts = SizedList()
        self._enums = SizedList()
        self._unions = SizedList()
        self._aggregates = SizedList()

    def asdict(self):
        d = {
            'name': self._name,
            'fqtn': self._fqtn,
            'filename': self.filename(),
            'stem': os.path.basename(self.filename()),
            'dirname': os.path.dirname(self.filename()),
            'package': self._package,
            'includes': [x.asdict() for x in self._includes],
            'modules': [x.asdict() for x in self._modules],
            'structs': [x.asdict() for x in self._structs],
            'typedefs': [x.asdict() for x in self._typedefs],
            'consts': [x.asdict() for x in self._consts],
            'enums': [x.asdict() for x in self._enums],
            'unions': [x.asdict() for x in self._unions],
            'aggregates': [x.asdict() for x in self._aggregates]
        }
        return d

    def includes(self):
        return self._includes

    def addInclude(self, v):
        self._includes.append(v)

    def modules(self):
        return self._modules

    def addModule(self, v):
        self._modules.append(v)

    def structs(self):
        return self._structs

    def addStruct(self, v):
        self._structs.append(v)

    def typedefs(self):
        return self._typedefs

    def addTypedef(self, v):
        self._typedefs.append(v)

    def consts(self):
        return self._consts

    def addConst(self, v):
        self._consts.append(v)

    def enums(self):
        return self._enums

    def addEnum(self, v):
        self._enums.append(v)

    def unions(self):
        return self._unions

    def addUnion(self, v):
        self._unions.append(v)

    def aggregates(self):
        return self._aggregates

    def setAggregates(self, aggregates):
        self._aggregates = aggregates

    def addAggregate(self, v):
        self._aggregates.append(v)

    def fqtn(self):
        return self._fqtn

    def package(self):
        return self._package

    def filename(self):
        return self._filename


class Include(Node):
    def __init__(self, parent, name, tree):
        super().__init__(parent, os.path.splitext(name)[0])
        self._filename = name
        self._tree = tree

    def asdict(self):
        d = {
            'name': self.name(),
            'filename': self.filename(),
            'tree': self.tree().asdict()
        }
        return d

    def filename(self):
        return self._filename

    def tree(self):
        return self._tree


class Module(Node):
    def __init__(self, parent, name):
        super().__init__(parent, name)
        self._modules = SizedList()
        self._structs = SizedList()
        self._typedefs = SizedList()
        self._consts = SizedList()
        self._enums = SizedList()
        self._directives = SizedList()
        self._subdirectives = SizedList()
        self._unions = SizedList()

    def asdict(self):
        d = {
            'name': self._name,
            'fqtn': self.fqtn(),
            'package': self.package(),
            'modules': [x.asdict() for x in self._modules],
            'structs': [x.asdict() for x in self._structs],
            'typedefs': [x.asdict() for x in self._typedefs],
            'consts': [x.asdict() for x in self._consts],
            'enums': [x.asdict() for x in self._enums],
            'directives': [x.asdict() for x in self._directives],
            'subdirectives': [x.asdict() for x in self._subdirectives],
            'unions': [x.asdict() for x in self._unions]
        }
        return d

    def modules(self):
        return self._modules

    def addModule(self, v):
        self._modules.append(v)

    def structs(self):
        return self._structs

    def addStruct(self, v):
        self._structs.append(v)

    def typedefs(self):
        return self._typedefs

    def addTypedef(self, v):
        self._typedefs.append(v)

    def consts(self):
        return self._consts

    def addConst(self, v):
        self._consts.append(v)

    def enums(self):
        return self._enums

    def addEnum(self, v):
        self._enums.append(v)

    def directives(self):
        return self._directives

    def addDirective(self, v):
        self._directives.append(v)

    def subdirectives(self):
        d = copy.deepcopy(self._subdirectives)
        self._subdirectives = SizedList()
        return d

    def addSubdirective(self, v):
        self._subdirectives.append(v)

    def unions(self):
        return self._unions

    def addUnion(self, v):
        self._unions.append(v)

    def fqtn(self):
        return self.package() + '.' + self._name

    def package(self):
        return self._parent.fqtn()


class Struct(Node):
    def __init__(self, parent, name, base_class=None, directives=SizedList(),
                 source_file=None):
        super().__init__(parent, name, source_file=source_file)
        self._base_class = base_class
        self._members = SizedList()
        # self._consts = SizedList()
        self._directives = directives
        self._subdirectives = SizedList()

    def asdict(self):
        def baseClassDict(base_class):
            if base_class is not None:
                return base_class
            return None
        d = {
            'name': self._name,
            'fqtn': self.fqtn(),
            'source_file': self.sourceFile(),
            'package': self.package(),
            'base_class': baseClassDict(self._base_class),
            'directives': [x.asdict() for x in self._directives],
            'subdirectives': [x.asdict() for x in self._subdirectives],
            'members': [x.asdict() for x in self._members]
        }
        return d

    def members(self):
        return self._members

    def addMember(self, v):
        self._members.append(v)

    def baseClass(self):
        return self._base_class

    def directives(self):
        return self._directives

    def addDirective(self, v):
        self._directives.append(v)

    def subdirectives(self):
        d = copy.deepcopy(self._subdirectives)
        self._subdirectives = SizedList()
        return d

    def addSubdirective(self, v):
        self._subdirectives.append(v)

    def fqtn(self):
        return self.package() + '.' + self._name

    def package(self):
        return self._parent.fqtn()


class Typedef(Node):
    def __init__(self, parent, name, utype, source_file=None):
        super().__init__(parent, name, source_file=source_file)
        self._type = utype

    def asdict(self):
        return {
            'name': self._name,
            'fqtn': self.fqtn(),
            'source_file': self.sourceFile(),
            'package': self.package(),
            'type': self._type.asdict()
        }

    def type(self):
        return self._type

    def fqtn(self):
        return self.package() + '.' + self._name

    def package(self):
        return self._parent.fqtn()


class Constant(Node):
    def __init__(self, parent, name, utype, value, source_file=None):
        super().__init__(parent, name, source_file=source_file)
        self._type = utype
        FLOAT_TYPES = ['double', 'float', 'float32', 'float64', 'longDouble']
        STR_LIKE_TYPES = [
            'string', 'wstring', 'char', 'wchar',
            'octet', 'char8', 'char16', 'byte'
        ]
        BOOLEAN_TYPES = ['boolean']
        if self.type().name() in FLOAT_TYPES:
            self._value = float(value)
        elif self.type().name() in STR_LIKE_TYPES:
            self._value = str(value)
        elif self.type().name() in BOOLEAN_TYPES:
            if isinstance(value, bool):
                self._value = value
            elif value.lower() not in ['true', 'false']:
                s = 'Boolean types must have the value of either '
                s += '\'true\' or \'false\'. Received: {}'.format(value)
                raise Exception(s)
            else:
                self._value = True if value.lower() == 'true' else False
        else:
            self._value = int(value)

    def asdict(self):
        return {
            'name': self._name,
            'fqtn': self.fqtn(),
            'source_file': self.sourceFile(),
            'package': self.package(),
            'value': self._value,
            'type': self._type.asdict()
        }

    def value(self):
        return self._value

    def type(self):
        return self._type

    def fqtn(self):
        return self.package() + '.' + self._name

    def package(self):
        return self._parent.fqtn()


class Member(Node):
    def __init__(self, parent, name, utype, optional=None):
        super().__init__(parent, name)
        self._type = utype
        self._optional = False
        if optional is not None:
            self._optional = optional

    def asdict(self):
        return {
            'name': self._name,
            'getter': self.getter(),
            'type': self._type.asdict(),
            'optional': self._optional
        }

    def type(self):
        return self._type

    def isOptional(self):
        return self._optional

    def getter(self):
        return 'mutable{}'.format(self._name[0].upper() + self._name[1:])


class UnionMember(Member):
    def __init__(self, parent, name, utype, descriminator):
        super().__init__(parent, name, utype)
        self._descriminator = descriminator

    def asdict(self):
        d = super().asdict()
        # this is the value of the discriminator
        d['discriminator'] = self.descriminator()
        return d

    def descriminator(self):
        return self._descriminator


class Enumeration(Node):
    def __init__(self, parent, name, source_file=None):
        super().__init__(parent, name, source_file=source_file)
        self._enumerators = SizedList()

    def asdict(self):
        d = {
            'name': self._name,
            'fqtn': self.fqtn(),
            'source_file': self.sourceFile(),
            'package': self.package(),
        }
        if len(self._enumerators) > 0:
            d['enumerators'] = [x.asdict() for x in self._enumerators]
        return d

    def enumerators(self):
        return self._enumerators

    def addEnumerator(self, e):
        self._enumerators.append(e)

    def fqtn(self):
        return self.package() + '.' + self._name

    def package(self):
        return self._parent.fqtn()


class Enumerator(Node):
    def __init__(self, parent, name, value=None):
        super().__init__(parent, name)
        if value is None:
            self._value = value
        else:
            self._value = int(value)

    def asdict(self):
        return {
            'name': self._name,
            'value': self._value
        }

    def value(self):
        return self._value

    def setValue(self, v):
        self._value = v


class Directive(Node):
    def __init__(self, parent, name, data=None):
        super().__init__(parent, name)
        self._data = data

    def asdict(self):
        return {
            'name': self._name,
            'data': self._data
        }

    def data(self):
        return self._data


class Discriminator(Node):
    def __init__(self, utype):
        super().__init__()
        self._type = utype

    def asdict(self):
        return {
            'type': self._type.asdict()
        }

    def type(self):
        return self._type


class Union(Node):
    def __init__(self, parent, name, discriminator, source_file=None):
        super().__init__(parent, name, source_file=source_file)
        # this is the dicriminator's type specification
        self._discriminator = discriminator
        self._members = SizedList()

    def asdict(self):
        d = {
            'name': self._name,
            'fqtn': self.fqtn(),
            'source_file': self.sourceFile(),
            'package': self.package(),
            'discriminator': self.discriminator().asdict(),
            'members': [x.asdict() for x in self._members]
        }
        return d

    def members(self):
        return self._members

    def addMember(self, v):
        self._members.append(v)

    def fqtn(self):
        return self.package() + '.' + self._name

    def package(self):
        return self._parent.fqtn()

    def discriminator(self):
        return self._discriminator


class Aggregate():
    def __init__(self, type, is_struct=False, is_union=False):
        self._type = type
        self._is_struct = is_struct
        self._is_union = is_union

    def asdict(self):
        d = {
            'name': self._type.name(),
            'fqtn': self._type.fqtn(),
            'is_struct': self.isStruct(),
            'is_union': self.isUnion(),
            'type': self._type.asdict()
        }
        return d

    def isStruct(self):
        return self._is_struct

    def isUnion(self):
        return self._is_union


PRIMITIVE_TYPES = [
    'boolean',
    'byte',
    'char8',
    'char16',
    'int8',
    'uint8',
    'int16',
    'uint16',
    'int32',
    'uint32',
    'int64',
    'uint64',
    'float32',
    'float64',
    'short',
    'long',
    'long long',
    'unsigned short',
    'unsigned long',
    'unsigned long long',
    'double',
    'float',
    'long double',
    'char',
    'wchar',
    'octet',
]

DEPRECATED_PRIMITIVE_TYPES = [
    'unsignedShort',
    'unsignedLong',
    'longLong',
    'unsignedLongLong',
    'longDouble'
]

# Note, char, wchar, and octet are not considered 'strings'
STRING_TYPES = [
    'string',
    'wstring',
]


class SimpleType():
    def __init__(self, type_name, length=None, is_sequence=False):
        if type_name is None:
            raise Exception('type_name is None. This is not valid!')
        self._type_name = type_name.replace('::', '.')
        self._length = length
        self._is_sequence = is_sequence
        self._fqtn = None
        self._package = None
        self._is_enum = None
        self._is_const = None
        self._is_struct = None
        self._is_typedef = None
        self._is_union = None
        if self._type_name in PRIMITIVE_TYPES:
            self._is_primitive = True
        elif self._type_name in DEPRECATED_PRIMITIVE_TYPES:
            self._is_primitive = True
        else:
            self._is_primitive = False
        self._is_string = self._type_name in STRING_TYPES
        if self.isPrimitive() or self.isString():
            self._is_enum = False
            self._is_struct = False
            self._is_typedef = False
            self._is_const = False
            self._is_union = False
            # finally, set the fqtn
            self.setFqtn(self._type_name)

    def asdict(self):
        d = {
            'name': self.name(),
            'fqtn': self.fqtn(),
            'package': self.package(),
            'is_primitive': self.isPrimitive(),
            'is_array': self.isArray(),
            'is_enum': self.isEnum(),
            'is_const': self.isConst(),
            'is_struct': self.isStruct(),
            'is_typedef': self.isTypedef(),
            'is_string': self.isString(),
            'is_sequence': self.isSequence(),
            'is_union': self.isUnion(),
            'user_defined': self.isUserDefined(),
            'length': self.length()
        }
        return d

    def name(self):
        return self._type_name

    def isPrimitive(self):
        return self._is_primitive

    def isArray(self):
        return self._length is not None

    def isString(self):
        return self._is_string

    def isSequence(self):
        return self._is_sequence

    def isUserDefined(self):
        return not (self.isPrimitive() or self.isString())

    def length(self):
        return self._length

    def setLength(self, length):
        self._length = length

    # These fields are set during type resolution in phsae 2 parsing
    def fqtn(self):
        return self._fqtn

    def setFqtn(self, fqtn):
        self._fqtn = fqtn
        self.setPackage('.'.join(fqtn.split('.')[:-1]))
        self._type_name = self._fqtn.split('.')[-1]

    def package(self):
        return self._package

    def setPackage(self, package):
        self._package = package

    def isEnum(self):
        return self._is_enum

    def setIsEnum(self):
        self._is_enum = True
        self._is_struct = False
        self._is_typedef = False
        self._is_const = False
        self._is_union = False

    def isConst(self):
        return self._is_const

    def setIsConst(self):
        self._is_const = True
        self._is_struct = False
        self._is_typedef = False
        self._is_enum = False
        self._is_union = False

    def isStruct(self):
        return self._is_struct

    def setIsStruct(self):
        self._is_struct = True
        self._is_const = False
        self._is_typedef = False
        self._is_enum = False
        self._is_union = False

    def isTypedef(self):
        return self._is_typedef

    def setIsTypedef(self):
        self._is_typedef = True
        self._is_struct = False
        self._is_const = False
        self._is_enum = False
        self._is_union = False

    def isUnion(self):
        return self._is_union

    def setIsUnion(self):
        self._is_typedef = False
        self._is_struct = False
        self._is_const = False
        self._is_enum = False
        self._is_union = True


class ArrayType(SimpleType):
    def __init__(self, inner_type, length):
        # TODO -- not sure if this class is actually needed...
        super().__init__(inner_type, length=length)
        self._inner_type = None

    def asdict(self):
        d = super().asdict()
        if self._inner_type is not None:
            d['type_name'] = self._inner_type.asdict()
        else:
            d['type_name'] = None
        return d
