<%!
import generator_functions as gf
%>\
// ${ctx['name']}.cpp
//
// Note: this file is auto-generated and should not be edited directly.

## Note purposly not using the gf function here because it will override special types and we don't want that here
<% DIRNAME = gf.removePrefix(ctx['dirname'],'idl').strip('/') %>\
% if DIRNAME != '':
#include "${ctx['package_name']}/${DIRNAME}/${ctx['name']}.hpp"
#include "${ctx['package_name']}/${DIRNAME}/detail/${ctx['name']}Serializer.hpp"
% else:
#include "${ctx['package_name']}/${ctx['name']}.hpp"
#include "${ctx['package_name']}/detail/${ctx['name']}Serializer.hpp"
% endif

% for el in ctx['includes']:
#include "${gf.getSerializerInclude(el, pkg=ctx['package'])}"
% endfor
% for el in gf.getAllUnions(ctx, []):
<% NAMESPACE = el['package'].strip('.').replace('.', '::') %>\
% if NAMESPACE != '':
<% UNIONNAME = '{}::{}::{}'.format(ctx['prefix'], NAMESPACE, el['name']) %>\
using namespace ${ctx['prefix']}::${NAMESPACE};
% else:
<% UNIONNAME = '{}::{}'.format(ctx['prefix'], el['name']) %>\
using namespace ${ctx['prefix']};
% endif

namespace auto_generated {

void serialize(const ${UNIONNAME}& obj, std::vector<std::uint8_t>& buf) {
   msgpack::pack(&buf.buffer(), obj);
}

void deserialize(const std::string_view buf, ${UNIONNAME}& obj) {
   msgpack::object_handle handle;
   msgpack::v3::unpack(handle, static_cast<const char*>(buf.data()), buf.size());
   msgpack::object object = handle.get();
   object.convert(obj);
}

}
% endfor

% for el in gf.getAllStructs(ctx, []):

<% NAMESPACE = el['package'].strip('.').replace('.', '::') %>\
% if NAMESPACE != '':
<% STRUCTNAME = '{}::{}::{}'.format(ctx['prefix'], NAMESPACE, el['name']) %>\
using namespace ${ctx['prefix']}::${NAMESPACE};
% else:
<% STRUCTNAME = '{}::{}'.format(ctx['prefix'], el['name']) %>\
using namespace ${ctx['prefix']};
% endif

namespace auto_generated {

void serialize(const ${STRUCTNAME}& obj, std::vector<std::uint8_t>& buf) {
   msgpack::pack(&buf.buffer(), obj);
}

void deserialize(const std::string_view buf, ${STRUCTNAME}& obj) {
   msgpack::object_handle handle;
   msgpack::v3::unpack(handle, static_cast<const char*>(buf.data()), buf.size());
   msgpack::object object = handle.get();
   object.convert(obj);
}

}
% endfor
% if len(gf.getAllEnums(ctx, [])) > 0:
namespace auto_generated {
% for el in gf.getAllEnums(ctx, []):
<% NAMESPACE = el['package'].strip('.').replace('.', '::') %>\
% if NAMESPACE != '':
<% ENUMNAME = '{}::{}::{}'.format(ctx['prefix'], NAMESPACE, el['name']) %>\
% else:
<% ENUMNAME = '{}::{}'.format(ctx['prefix'], el['name']) %>\
% endif
std::string EnumUtil<${ENUMNAME}>::toString(const ${ENUMNAME}& e) {

   switch (e) {
   % for en in el['enumerators']:
      case ${ENUMNAME}::${en['name']}: {
         return "${en['name']}";
      }
   %endfor
      default: {
         return fmt::format("UNKNOWN ENUM VALUE RECEIVED: {}", static_cast<int>(e));
      }
   }
   return fmt::format("UNKNOWN ENUM VALUE RECEIVED: {}", static_cast<int>(e));
}

std::optional<${ENUMNAME}> EnumUtil<${ENUMNAME}>::fromString(const std::string& s) {

   % for en in el['enumerators']:
   if (s == "${en['name']}") {
      return ${ENUMNAME}::${en['name']};
   }
   %endfor

   return {};
}
%endfor

}
% endif