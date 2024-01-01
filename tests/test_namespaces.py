#!/usr/bin/env python
#
# Copyright (c), 2016-2020, SISSA (International School for Advanced Studies).
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
#
# @author Davide Brunato <brunato@sissa.it>
#
import unittest
import os
import copy

from xmlschema.names import XSD_NAMESPACE, XSI_NAMESPACE
from xmlschema.namespaces import NamespaceResourcesMap, NamespaceMapper, NamespaceView


CASES_DIR = os.path.join(os.path.dirname(__file__), '../test_cases')


class TestNamespaceResourcesMap(unittest.TestCase):

    def test_init(self):
        nsmap = [('tns0', 'schema1.xsd')]
        self.assertEqual(NamespaceResourcesMap(), {})
        self.assertEqual(NamespaceResourcesMap(nsmap), {'tns0': ['schema1.xsd']})
        nsmap.append(('tns0', 'schema2.xsd'))
        self.assertEqual(NamespaceResourcesMap(nsmap), {'tns0': ['schema1.xsd', 'schema2.xsd']})

    def test_repr(self):
        namespaces = NamespaceResourcesMap()
        namespaces['tns0'] = 'schema1.xsd'
        namespaces['tns1'] = 'schema2.xsd'
        self.assertEqual(repr(namespaces), "{'tns0': ['schema1.xsd'], 'tns1': ['schema2.xsd']}")

    def test_dictionary_methods(self):
        namespaces = NamespaceResourcesMap()
        namespaces['tns0'] = 'schema1.xsd'
        namespaces['tns1'] = 'schema2.xsd'
        self.assertEqual(namespaces, {'tns0': ['schema1.xsd'], 'tns1': ['schema2.xsd']})

        self.assertEqual(len(namespaces), 2)
        self.assertEqual(set(x for x in namespaces), {'tns0', 'tns1'})

        del namespaces['tns0']
        self.assertEqual(namespaces, {'tns1': ['schema2.xsd']})
        self.assertEqual(len(namespaces), 1)

        namespaces.clear()
        self.assertEqual(namespaces, {})


class TestNamespaceMapper(unittest.TestCase):

    def test_init(self):
        namespaces = dict(xs=XSD_NAMESPACE, xsi=XSI_NAMESPACE)
        mapper = NamespaceMapper(namespaces)
        self.assertEqual(mapper, namespaces)
        self.assertIsNot(namespaces, mapper.namespaces)

    def test_dictionary_methods(self):
        namespaces = dict(xs=XSD_NAMESPACE)
        mapper = NamespaceMapper(namespaces)

        mapper['xsi'] = XSI_NAMESPACE
        self.assertEqual(mapper, dict(xs=XSD_NAMESPACE, xsi=XSI_NAMESPACE))

        del mapper['xs']
        self.assertEqual(len(mapper), 1)
        self.assertEqual(mapper, dict(xsi=XSI_NAMESPACE))

        mapper.clear()
        self.assertEqual(mapper, {})

    def test_process_namespaces(self):
        namespaces = dict(xs=XSD_NAMESPACE, xsi=XSI_NAMESPACE)

        mapper = NamespaceMapper(namespaces, process_namespaces=True)
        self.assertEqual(mapper.map_qname('{%s}name' % XSD_NAMESPACE), 'xs:name')
        self.assertEqual(mapper.map_qname('{unknown}name'), '{unknown}name')

        mapper = NamespaceMapper(namespaces, process_namespaces=False)
        self.assertEqual(mapper.map_qname(f'{XSD_NAMESPACE}name'), f'{XSD_NAMESPACE}name')
        self.assertEqual(mapper.map_qname('{unknown}name'), '{unknown}name')

    def test_strip_namespaces_and_process_namespaces(self):
        namespaces = dict(xs=XSD_NAMESPACE, xsi=XSI_NAMESPACE)

        mapper = NamespaceMapper(namespaces, strip_namespaces=False)
        self.assertFalse(mapper.strip_namespaces)
        self.assertTrue(mapper.process_namespaces)
        self.assertTrue(mapper._use_namespaces)
        self.assertEqual(mapper.map_qname('{%s}name' % XSD_NAMESPACE), 'xs:name')
        self.assertEqual(mapper.map_qname('{unknown}name'), '{unknown}name')

        mapper = NamespaceMapper(namespaces, strip_namespaces=True)
        self.assertTrue(mapper.strip_namespaces)
        self.assertTrue(mapper.process_namespaces)
        self.assertFalse(mapper._use_namespaces)
        self.assertEqual(mapper.map_qname('{%s}name' % XSD_NAMESPACE), 'name')
        self.assertEqual(mapper.map_qname('{unknown}name'), 'name')

        mapper = NamespaceMapper(namespaces, process_namespaces=False, strip_namespaces=True)
        self.assertEqual(mapper.map_qname('{%s}name' % XSD_NAMESPACE), 'name')
        self.assertEqual(mapper.map_qname('{unknown}name'), 'name')

    def test_copy(self):
        namespaces = dict(xs=XSD_NAMESPACE, xsi=XSI_NAMESPACE)

        mapper = NamespaceMapper(namespaces, strip_namespaces=True)
        other = copy.copy(mapper)

        self.assertIsNot(mapper.namespaces, other.namespaces)
        self.assertDictEqual(mapper.namespaces, other.namespaces)

    def test_default_namespace(self):
        namespaces = dict(xs=XSD_NAMESPACE, xsi=XSI_NAMESPACE)
        mapper = NamespaceMapper(namespaces)

        self.assertIsNone(mapper.default_namespace)
        mapper[''] = 'tns0'
        self.assertEqual(mapper.default_namespace, 'tns0')

    def test_push_and_pop_namespaces(self):
        namespaces = dict(xs=XSD_NAMESPACE, xsi=XSI_NAMESPACE)
        mapper = NamespaceMapper(namespaces)

        self.assertEqual(len(mapper._namespaces), 2)
        self.assertEqual(len(mapper._contexts), 0)

        mapper.pop_namespaces(0)

        internal_map = mapper.namespaces
        self.assertDictEqual(internal_map, {'xs': XSD_NAMESPACE, 'xsi': XSI_NAMESPACE})

        mapper.push_namespaces(3, [('tns0', XSD_NAMESPACE)])
        self.assertDictEqual(
            internal_map, {'xs': XSD_NAMESPACE, 'xsi': XSI_NAMESPACE, 'tns0': XSD_NAMESPACE}
        )
        self.assertIs(internal_map, mapper.namespaces)
        self.assertDictEqual(
            mapper._uri_to_prefix, {XSD_NAMESPACE: 'tns0', XSI_NAMESPACE: 'xsi'}
        )

        self.assertEqual(len(mapper._contexts), 1)
        mapper.pop_namespaces(5)
        self.assertEqual(len(mapper._contexts), 1)
        mapper.pop_namespaces(3)
        self.assertEqual(len(mapper._contexts), 0)

        mapper.push_namespaces(3, [('tns0', XSD_NAMESPACE)])
        self.assertEqual(len(mapper._contexts), 1)
        mapper.push_namespaces(5, [('tns1', 'foo')])
        self.assertEqual(len(mapper._contexts), 2)
        mapper.push_namespaces(6, [('tns2', 'bar')])
        self.assertEqual(len(mapper._contexts), 3)

        mapper.push_namespaces(4, [('tns3', 'foo')])
        self.assertEqual(len(mapper._contexts), 2)

    def test_map_qname(self):
        namespaces = dict(xs=XSD_NAMESPACE, xsi=XSI_NAMESPACE)
        mapper = NamespaceMapper(namespaces)

        mapper[''] = XSD_NAMESPACE
        self.assertEqual(mapper.map_qname(''), '')
        self.assertEqual(mapper.map_qname('foo'), 'foo')
        self.assertEqual(mapper.map_qname('{%s}element' % XSD_NAMESPACE), 'element')
        mapper.pop('')
        self.assertEqual(mapper.map_qname('{%s}element' % XSD_NAMESPACE), 'xs:element')

        with self.assertRaises(ValueError) as ctx:
            mapper.map_qname('{%selement' % XSD_NAMESPACE)
        self.assertIn("invalid value", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            mapper.map_qname('{%s}element}' % XSD_NAMESPACE)
        self.assertIn("invalid value", str(ctx.exception))

        with self.assertRaises(TypeError) as ctx:
            mapper.map_qname(None)
        self.assertIn("must be a string-like object", str(ctx.exception))

        with self.assertRaises(TypeError) as ctx:
            mapper.map_qname(99)
        self.assertIn("must be a string-like object", str(ctx.exception))

        mapper = NamespaceMapper(namespaces, process_namespaces=False)
        self.assertEqual(mapper.map_qname('bar'), 'bar')
        self.assertEqual(mapper.map_qname('xs:bar'), 'xs:bar')

        mapper = NamespaceMapper(namespaces, strip_namespaces=True)
        self.assertEqual(mapper.map_qname('bar'), 'bar')
        self.assertEqual(mapper.map_qname('xs:bar'), 'bar')

    def test_unmap_qname(self):
        namespaces = dict(xs=XSD_NAMESPACE, xsi=XSI_NAMESPACE)
        mapper = NamespaceMapper(namespaces)

        self.assertEqual(mapper.unmap_qname(''), '')
        self.assertEqual(mapper.unmap_qname('xs:element'), '{%s}element' % XSD_NAMESPACE)
        self.assertEqual(mapper.unmap_qname('{foo}bar'), '{foo}bar')
        self.assertEqual(mapper.unmap_qname('xsd:element'), 'xsd:element')

        with self.assertRaises(ValueError) as ctx:
            mapper.unmap_qname('xs::element')
        self.assertIn("invalid value", str(ctx.exception))

        with self.assertRaises(TypeError) as ctx:
            mapper.unmap_qname(None)
        self.assertIn("must be a string-like object", str(ctx.exception))

        with self.assertRaises(TypeError) as ctx:
            mapper.unmap_qname(99)
        self.assertIn("must be a string-like object", str(ctx.exception))

        self.assertEqual(mapper.unmap_qname('element'), 'element')
        mapper[''] = 'foo'
        self.assertEqual(mapper.unmap_qname('element'), '{foo}element')
        self.assertEqual(mapper.unmap_qname('element', name_table=['element']), 'element')

        mapper._strip_namespaces = True  # don't do tricks, create a new instance ...
        self.assertEqual(mapper.unmap_qname('element'), '{foo}element')

        mapper = NamespaceMapper(namespaces, process_namespaces=False)
        self.assertEqual(mapper.unmap_qname('bar'), 'bar')
        self.assertEqual(mapper.unmap_qname('xs:bar'), 'xs:bar')

        mapper = NamespaceMapper(namespaces, strip_namespaces=True)
        self.assertEqual(mapper.unmap_qname('bar'), 'bar')
        self.assertEqual(mapper.unmap_qname('xs:bar'), 'bar')


class TestNamespaceView(unittest.TestCase):

    def test_init(self):
        qnames = {'{tns0}name0': 0, '{tns1}name1': 1, 'name2': 2}
        ns_view = NamespaceView(qnames, 'tns1')
        self.assertEqual(ns_view, {'name1': 1})

    def test_repr(self):
        qnames = {'{tns0}name0': 0, '{tns1}name1': 1, 'name2': 2}
        ns_view = NamespaceView(qnames, 'tns0')
        self.assertEqual(repr(ns_view), "NamespaceView({'name0': 0})")

    def test_contains(self):
        qnames = {'{tns0}name0': 0, '{tns1}name1': 1, 'name2': 2}
        ns_view = NamespaceView(qnames, 'tns1')

        self.assertIn('name1', ns_view)
        self.assertNotIn('{tns1}name1', ns_view)
        self.assertNotIn('{tns0}name0', ns_view)
        self.assertNotIn('name0', ns_view)
        self.assertNotIn('name2', ns_view)
        self.assertNotIn(1, ns_view)

    def test_as_dict(self):
        qnames = {'{tns0}name0': 0, '{tns1}name1': 1, '{tns1}name2': 2, 'name3': 3}
        ns_view = NamespaceView(qnames, 'tns1')
        self.assertEqual(ns_view.as_dict(), {'name1': 1, 'name2': 2})
        self.assertEqual(ns_view.as_dict(True), {'{tns1}name1': 1, '{tns1}name2': 2})

        ns_view = NamespaceView(qnames, '')
        self.assertEqual(ns_view.as_dict(), {'name3': 3})
        self.assertEqual(ns_view.as_dict(True), {'name3': 3})


if __name__ == '__main__':
    import platform
    header_template = "Test xmlschema namespaces with Python {} on {}"
    header = header_template.format(platform.python_version(), platform.platform())
    print('{0}\n{1}\n{0}'.format("*" * len(header), header))

    unittest.main()
