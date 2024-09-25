<%!
import generator_functions as gf
%>\
// ${ctx['name']}.hpp
//
// Note: this file is auto-generated and should not be edited directly.

#pragma once

#include <type_traits>
#include <algorithm>
#include <cstdint>
#include <vector>
#include <string>
#include <array>
#include <string_view>
#include <optional>
#include <variant>
#include <memory>
<% PREFIX = ctx['prefix'] %>\

% for el in ctx['includes']:
#include "${gf.getInclude(el, pkg=ctx['package'])}"
% endfor

% for el in gf.getAllConsts(ctx, []):
<% NAMESPACE = el['package'].strip('.').replace('.', '::') %>\
% if NAMESPACE != '':
namespace ${PREFIX}::${NAMESPACE} {
% else:
namespace ${PREFIX} {
% endif
% if el['type']['is_string']:
static const ${gf.getType(el['type'], ctx['prefix'])} ${el['name']} = "${el['value']}";
% else:
constexpr ${gf.getType(el['type'], ctx['prefix'])} ${el['name']} = ${el['value']};
%endif
}

% endfor
% for el in gf.getAllTypedefs(ctx, []):
<% NAMESPACE = el['package'].strip('.').replace('.', '::') %>\
% if NAMESPACE != '':
namespace ${PREFIX}::${NAMESPACE} {
% else:
namespace ${PREFIX} {
%endif
using ${el['name']} = ${gf.getType(el['type'], ctx['prefix'])};
}

% endfor
% for el in gf.getAllEnums(ctx, []):
<% NAMESPACE = el['package'].strip('.').replace('.', '::') %>\
% if NAMESPACE != '':
namespace ${PREFIX}::${NAMESPACE} {
% else:
namespace ${PREFIX} {
%endif
enum class ${el['name']} {
   % for en in el['enumerators']:
     % if en['value'] is not None:
<% lastval = en['value'] %>\
       % if not loop.last:
   ${en['name']} = ${en['value']},
       % else:
   ${en['name']} = ${en['value']}
       % endif
     % else:
       % if not loop.last:
   ${en['name']} = ${lastval+1},
       % else:
   ${en['name']} = ${lastval+1}
       % endif
<% lastval = loop.index %>\
     % endif
   % endfor
};
}

% endfor

% for agg in ctx['aggregates']:
%  if agg['is_struct']:
<% el = agg['type'] %>
<% NAMESPACE = el['package'].strip('.').replace('.', '::') %>\
% if NAMESPACE != '':
<% STRUCTNAME = '{}::{}::{}'.format(PREFIX, NAMESPACE, el['name']) %>\
namespace ${PREFIX}::${NAMESPACE} {
% else:
<% STRUCTNAME = '{}::{}'.format(PREFIX, el['name']) %>\
namespace ${PREFIX} {
% endif
% if el['base_class'] is not None:
class ${el['name']} : public ${gf.getLangType(el['base_class']['name'], ctx['prefix'])} {
% else:
class ${el['name']} {
% endif
public:

   using Ptr = std::shared_ptr<${el['name']}>;
   using ConstPtr = std::shared_ptr<${el['name']} const>;

   ${el['name']}() {}

   % if len(el['members']) > 0:
     % if len(el['members']) == 1:
   explicit ${el['name']}(
     % else:
   ${el['name']}(
     % endif
     % for mem in el['members']:
<% langtype = gf.getType(mem['type'], ctx['prefix'], mem['optional'])%>\
       % if not loop.last:
      ${langtype} ${mem['name']},
       % else:
      ${langtype} ${mem['name']}),
       % endif
     % endfor
     % for mem in el['members']:
   <% langtype = gf.getType(mem['type'], ctx['prefix'], mem['optional'])%>\
       % if not loop.last:
         ${mem['name']}_(std::move(${mem['name']})),
       % else:
         ${mem['name']}_(std::move(${mem['name']})) {}
       % endif
     % endfor
   % endif

   ~${el['name']}() noexcept {}

   ${el['name']}(const ${el['name']}&) = default;
   ${el['name']}(${el['name']}&&) noexcept = default;
   ${el['name']}& operator=(const ${el['name']}&) = default;
   ${el['name']}& operator=(${el['name']}&&) noexcept = default;

   friend void swap(${STRUCTNAME}& a,
                    ${STRUCTNAME}& b) noexcept {
      using std::swap;
   % for mem in el['members']:
      swap(a.${mem['name']}_, b.${mem['name']}_);
   % endfor
   }
   % for mem in el['members']:
<% langtype = gf.getType(mem['type'], ctx['prefix'], mem['optional'])%>
   void ${mem['name']}(${gf.getType(mem['type'], ctx['prefix'])} in) { ${mem['name']}_ = std::move(in); }
   % if gf.isSequence(mem['type']):
   % if mem['optional']:
   void ${gf.getAppender(mem['name'])}(${gf.getLangType(mem['type']['fqtn'], ctx['prefix'])} in) {
      if (!${mem['name']}_) ${mem['name']}_ = {};
      ${mem['name']}_->push_back(std::move(in));
   }
   % else:
   void ${gf.getAppender(mem['name'])}(${gf.getLangType(mem['type']['fqtn'], ctx['prefix'])} in) { ${mem['name']}_.push_back(std::move(in)); }
   % endif
   % endif
<% UNION = gf.getUnion(mem, ctx) %>\
   % if UNION is not None:
   % for unionMem in UNION['members']:
   void ${mem['name']}(const ${gf.getType(unionMem['type'], ctx['prefix'])}& in) { ${mem['name']}_ = std::move(in); }
   % endfor
   % endif
   [[nodiscard]] const ${langtype}& ${mem['name']}() const { return ${mem['name']}_; }
   [[nodiscard]] ${langtype}& ${mem['getter']}() { return ${mem['name']}_; }
   % endfor

   [[nodiscard]] std::string_view getFqtn() const { return "${STRUCTNAME}"; }

   static constexpr std::size_t NUM_MEMBERS = ${len(el['members'])};

private:
   % for mem in el['members']:
<% langtype = gf.getType(mem['type'], ctx['prefix'], mem['optional'])%>\
   ${langtype} ${mem['name']}_ {};
   % endfor
};

}

namespace auto_generated {

/**
 * This is a helper struct to return the fully qualified type name of
 * this structure as a string. This is useful in many cases when
 * publishing or subscribing to messages or when logging information.
 */
% if NAMESPACE != '':
<% STRUCTNAME = '{}::{}::{}'.format(PREFIX, NAMESPACE, el['name']) %>\
% else:
<% STRUCTNAME = '{}::{}'.format(PREFIX, el['name']) %>\
% endif
template<>
struct fully_qualified_type_name<${STRUCTNAME}> {
   static constexpr char value_[] = "${STRUCTNAME}";
   static constexpr auto value = std::string_view(value_);
};

}

namespace aut_generated {

void serialize(const ${STRUCTNAME}& obj, std::vector<std::uint8_t>& buf);

void deserialize(const std::string_view buf, ${STRUCTNAME}& obj);

}
%  elif agg['is_union']:
<% el = agg['type'] %>
<% NAMESPACE = el['package'].strip('.').replace('.', '::') %>\
% if NAMESPACE != '':
namespace ${PREFIX}::${NAMESPACE} {
% else:
namespace ${PREFIX} {
% endif
   using ${el['name']} = std::variant<
   % for mem in el['members']:
<% langtype = gf.getType(mem['type'], ctx['prefix'], mem['optional'])%>\
% if loop.last:
      ${langtype}
% else:
      ${langtype},
% endif
   % endfor
   >;
}
%  endif

% endfor

% if len(gf.getAllEnums(ctx, [])) > 0:
namespace auto_generated {
% for el in gf.getAllEnums(ctx, []):
<% NAMESPACE = el['package'].strip('.').replace('.', '::') %>\
template<>
% if NAMESPACE != '':
struct EnumUtil<${PREFIX}::${NAMESPACE}::${el['name']}> {

   using E = ${PREFIX}::${NAMESPACE}::${el['name']};
%else:
struct EnumUtil<${el['name']}> {

   using E = ${el['name']};
%endif

   static std::string toString(const E& e);
   static std::optional<E> fromString(const std::string& s);
};

%endfor
}
% endif