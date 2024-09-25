<%!
import generator_functions as gf
%>\
// ${gf.getSerializerInclude(ctx, pkg=ctx['package_name'])}
//
// Note: this file is auto-generated and should not be edited directly.

#pragma once

#include "${gf.getInclude(ctx, pkg=ctx['package_name'])}"
% for el in ctx['includes']:
#include "${gf.getSerializerInclude(el, pkg=ctx['package_name'])}"
% endfor
#include <stdexcept>

#include <msgpack.hpp>

% for el in gf.getAllEnums(ctx, []):
<% NAMESPACE = el['package'].strip('.').replace('.', '::') %>\
% if NAMESPACE != '':
MSGPACK_ADD_ENUM(${ctx['prefix']}::${NAMESPACE}::${el['name']})
% else:
MSGPACK_ADD_ENUM(${ctx['prefix']}::${el['name']})
% endif

% endfor
% for el in gf.getAllUnions(ctx, []):
<% NAMESPACE = el['package'].strip('.').replace('.', '::') %>\
% if NAMESPACE != '':
<% UNIONNAME = '{}::{}::{}'.format(ctx['prefix'], NAMESPACE, el['name']) %>\
% else:
<% UNIONNAME = '{}::{}'.format(ctx['prefix'], el['name']) %>\
% endif
namespace msgpack {
MSGPACK_API_VERSION_NAMESPACE(MSGPACK_DEFAULT_API_NS) {
namespace adaptor {

template <>
struct convert<${UNIONNAME}> {
   msgpack::object const& operator()(msgpack::object const& o, ${UNIONNAME}& m) const {

      // convert from msgpack::object to T
      if (o.type != msgpack::type::ARRAY) {
         auto s = fmt::format("Received invalid msgpack object type: {}", o.type);
         std::cerr << s << "\n";
         throw std::invalid_argument(s);
      }

      if (o.via.array.size != 2) {
         auto s = fmt::format("Received msgpack object for ${UNIONNAME} with {} elements. Expected {}",
                              o.via.array.size, 2);
         std::cerr << s << "\n";
         throw std::invalid_argument(s);
      }

   int index = o.via.array.ptr[0].as<int>();
   switch (index) {
   % for mem in el['members']:
<% langtype = gf.getType(mem['type'], ctx['prefix'], mem['optional'])%>\
      case ${loop.index}:
         m = o.via.array.ptr[1].as<${langtype}>();
         break;
   % endfor
      default:
         auto s = fmt::format("Received msgpack object for union with index {}, max {}",
                              index, ${len(el['members'])});
         std::cerr << s << "\n";
         throw std::invalid_argument(s);
      }
      return o;
   }
};

template <>
struct pack<${UNIONNAME}> {
   template <typename Stream>
   msgpack::packer<Stream>& operator()(msgpack::packer<Stream>& p, const ${UNIONNAME}& m) const {

      // convert from T to msgpack::packer<Stream>
      p.pack_array(2);   // unions always have two objects - an index and the data
      const int index = m.index();
      p.pack(index);
      switch(index) {
      % for mem in el['members']:
         case ${loop.index}:
<% langtype = gf.getType(mem['type'], ctx['prefix'], mem['optional'])%>\
            p.pack(std::get<${langtype}>(m));
            break;
      %endfor
         default:
            auto s = fmt::format("Received msgpack object for union with index {}, max {}",
                              index, ${len(el['members'])});
            std::cerr << s << "\n";
            throw std::invalid_argument(s);
      }
      return p;
   }
};

} // namespace adaptor
} // MSGPACK_API_VERSION_NAMESPACE(MSGPACK_DEFAULT_API_NS)
} // namespace msgpack
% endfor
% for el in gf.getAllStructs(ctx, []):
<% NAMESPACE = el['package'].strip('.').replace('.', '::') %>\
% if NAMESPACE != '':
<% STRUCTNAME = '{}::{}::{}'.format(ctx['prefix'], NAMESPACE, el['name']) %>\
% else:
<% STRUCTNAME = '{}::{}'.format(ctx['prefix'], el['name']) %>\
% endif
namespace msgpack {
MSGPACK_API_VERSION_NAMESPACE(MSGPACK_DEFAULT_API_NS) {
namespace adaptor {

template <>
struct convert<${STRUCTNAME}> {
   msgpack::object const& operator()(msgpack::object const& o, ${STRUCTNAME}& m) const {

      // convert from msgpack::object to T
      if (o.type != msgpack::type::ARRAY) {
         auto s = fmt::format("Received invalid msgpack object type: {}", o.type);
         std::cerr << s << "\n";
         throw std::invalid_argument(s);
      }

      if (o.via.array.size != ${STRUCTNAME}::NUM_MEMBERS) {
         auto s = fmt::format("Received msgpack object for ${STRUCTNAME} with {} elements. Expected {}",
                              o.via.array.size, ${STRUCTNAME}::NUM_MEMBERS);
         std::cerr << s << "\n";
         throw std::invalid_argument(s);
      }

   % for mem in el['members']:
      o.via.array.ptr[${loop.index}] >> m.${mem['getter']}();
   % endfor

      return o;
   }
};

template <>
struct pack<${STRUCTNAME}> {
   template <typename Stream>
   msgpack::packer<Stream>& operator()(msgpack::packer<Stream>& p, const ${STRUCTNAME}& m) const {

      // convert from T to msgpack::packer<Stream>
      p.pack_array(${STRUCTNAME}::NUM_MEMBERS);
   % for mem in el['members']:
      p.pack(m.${mem['name']}());
   % endfor
      return p;
   }
};

} // namespace adaptor
} // MSGPACK_API_VERSION_NAMESPACE(MSGPACK_DEFAULT_API_NS)
} // namespace msgpack
% endfor