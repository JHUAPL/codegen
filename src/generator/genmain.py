
import os
import sys
import json
import uuid
from pathlib import Path
import inspect
import logging
from generator import IdlProcessor
from mako.template import Template


sys.path.insert(1, os.path.dirname(os.path.realpath(__file__)))
logger = logging.getLogger('parser')


def debug(msg):
    _, _, _, _, lines, _ = inspect.getouterframes(
        inspect.currentframe())[1]
    line = lines[0]
    indentation_level = line.find(line.lstrip())
    logger.debug('{i} [{m}]'.format(i='.'*indentation_level, m=msg))


def info(msg):
    _, _, _, _, lines, _ = inspect.getouterframes(
        inspect.currentframe())[1]
    line = lines[0]
    indentation_level = line.find(line.lstrip())
    logger.info('{i} [{m}]'.format(i='.'*indentation_level, m=msg))


def getOutputFile(template, source, args):
    od = args.output_root
    if source is None:
        s = 'Source not set for template: {}'.format(template)
        raise Exception(s)
    bn = os.path.basename(source).split('.')[0]
    # build a mapping from the template type to the output file name
    # this could be more elegant
    if 'header.mako' in template:
        return os.path.join(od, '{}.hpp'.format(bn))
    if 'serialization.mako' in template:
        return os.path.join(od, 'detail', '{}Serializer.hpp'.format(bn))
    if 'implementation.mako' in template:
        return os.path.join(od, '{}.cpp'.format(bn))
    s = 'Unknown template: {}'.format(template)
    raise Exception(s)


def processTemplate(template, node, args, stems, payload=None):
    debug('Using template {}'.format(template))
    ctx = {}
    outputfile = ''
    if node is None:
        outputfile = getOutputFile(template, None, args)
    else:
        ctx = node.asdict()
        outputfile = getOutputFile(template, node.filename(), args)
    pparts = args.output_root.split(os.path.sep)
    tp = outputfile.replace(args.output_root + '/', '')
    last = pparts[-1]
    tp = os.path.join(last, tp)
    ctx['package_name'] = args.pkg_name
    ctx['package_name_internal'] = args.pkg_name_internal
    ctx['messages'] = stems
    # if 'idl' in ctx['package']:
    ctx['package'] = args.pkg_name
    ctx['prefix'] = args.ns_prefix
    # print('PACKAGE: ', ctx['package'])
    ctx['msg_dependencies'] = args.msg_dependencies
    if payload is not None:
        ctx['payload'] = payload
    module_dir = os.path.join('/tmp', 'mako_modules', uuid.uuid4().hex[:16])
    tmpl = Template(filename=str(template), module_directory=module_dir)
    s = tmpl.render(ctx=ctx)
    debug(outputfile)
    if not os.path.isdir(os.path.dirname(outputfile)):
        os.makedirs(os.path.dirname(outputfile), exist_ok=True)
    with open(outputfile, "w+") as ofile:
        ofile.write(s)


def processTemplates(node, templates, stems, args):
    if templates is not None:
        for filename in templates:
            processTemplate(filename, node, args, stems)
    if args.json:
        if not os.path.isdir(os.path.join(args.output_root, 'json')):
            os.makedirs(os.path.join(args.output_root, 'json'))
        ofile = '{}.json'.format(node.name())
        with open(os.path.join(args.output_root, 'json', ofile), 'w') as f:
            json.dump(node.asdict(), f, indent=4)


def genmain(args):
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    os.environ['PROJECT_PATH'] = args.types_path

    templates = []
    if args.template_name is not None:
        for tn in args.template_name:
            templates.append(tn)
    if args.template_dir is not None:
        for d in args.template_dir:
            sharks = Path(d).rglob('*.mako')
            templates = templates + [str(x) for x in sharks]
        if len(templates) == 0:
            s = 'No templates found in template directory '
            s += '\'{}\''.format(args.template_dir)
            e = Exception(s)
            raise e
    prsr = IdlProcessor(args.include_dir)
    sources = args.sources
    debug(sources)

    pkg_spec = {}
    with open(args.pkg_spec) as f:
        pkg_spec = json.load(f)
    if 'pkg_name' in pkg_spec:
        args.pkg_name_internal = pkg_spec['pkg_name']
    else:
        s = """Must specify 'pkg_name' in pkg_spec.json for """
        s += args.pkg_name
        raise Exception(s)

    if 'msg_dependencies' in pkg_spec:
        args.msg_dependencies = pkg_spec['msg_dependencies']
    else:
        s = """Must specify 'msg_dependencies' in pkg_spec.json for """
        s += args.pkg_name
        raise Exception(s)

    srcs = sources
    sources = []
    for src in srcs:
        if os.path.isfile(src):
            sources.append(src)
    sources.sort()
    stems = [x.split(os.sep)[-1].replace('.idl', '') for x in sources]
    debug(sources)
    for src in sources:
        if not os.path.exists(src):
            raise Exception('File not found: {}'.format(src))
        print('gen.py:\t{}'.format(src))
        node = prsr.processFile(src)
        processTemplates(node, templates, stems, args)
