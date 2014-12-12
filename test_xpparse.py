""" Test module to parse xprotocl text
"""

import xpparse as xpp

from pyparsing import ParseException

from nose.tools import (assert_true, assert_false, assert_equal,
                        assert_not_equal, assert_raises)


def assert_tokens(pattern, source, expected):
    assert_equal(pattern.parseString(source).asList(), expected)


def test_xprotocol():
    assert_tokens(xpp.xprotocol_tag, '<xprotocol>', ['xprotocol'])
    assert_tokens(xpp.xprotocol_tag, '<   xprotocol >', ['xprotocol'])
    assert_tokens(xpp.xprotocol_tag, '<   xProtoCol >', ['xprotocol'])
    assert_raises(ParseException, xpp.xprotocol_tag.parseString, '<yprotocol>')
    assert_raises(ParseException, xpp.xprotocol_tag.parseString, '<yprotocol ')


def test_strings_newlines():
    assert_tokens(xpp.quoted_multi, '"A string"', ['A string'])
    assert_tokens(xpp.quoted_multi, '"A ""string"', ['A ""string'])
    assert_tokens(xpp.quoted_multi,
                  '"A multi\n\nline\n\nlong string with\n""Double quotes"""',
                  ['A multi\n\nline\n\nlong string with\n""Double quotes""'])


def test_attributes():
    assert_tokens(xpp.string_attr,
                  '<Name> "PhoenixMetaProtocol"',
                  ['Name', 'PhoenixMetaProtocol'])
    # Int returns int
    assert_tokens(xpp.int_attr,
                  '<ID> 1000002 ',
                  ['ID', 1000002])
    # Float returns float
    assert_tokens(xpp.float_attr,
                  '<Userversion> 2.0 ',
                  ['Userversion', 2.0])
    # True / False constants
    assert_tokens(xpp.true, '"true"', [True])
    assert_tokens(xpp.false, '"false"', [False])
    # Bool returns True | False
    assert_tokens(xpp.bool_, ' "false" ', [False])
    assert_tokens(xpp.bool_, ' "true" ', [True])
    # Key value returns tuple, with converted values
    assert_tokens(xpp.key_value, '<thing> "true" ', [('thing', True)])
    assert_tokens(xpp.key_value, '<other> "string" ', [('other', "string")])
    assert_tokens(xpp.key_value, '< some> 2.3 ', [('some', 2.3)])
    # Lists can contain any of the above
    assert_tokens(xpp.list_value,
                  '{ "false" "true" 1 "three" }',
                  [[False, True, 1, "three"]])
    assert_tokens(xpp.list_value,
                  '{ "false" "true" 1 "three" }',
                  [[False, True, 1, "three"]])
    assert_tokens(xpp.list_value,
                  '{ "false" "true" <here> "there" 3 10.4 }',
                  [[False, True, ('here', 'there'), 3, 10.4]])
    # Attrs are tags followed by the various variable types
    assert_tokens(xpp.bool_attr, '<SomeName> "false" ', ['SomeName', False])
    assert_tokens(xpp.bool_attr, '<Name> "true" ', ['Name', True])
    assert_tokens(xpp.float_attr, '<SomeName> 2.3', ['SomeName', 2.3])
    assert_tokens(xpp.int_attr, '<SomeName> 3', ['SomeName', 3])
    assert_tokens(xpp.string_attr,
                  '<Label> "Inline Composing"',
                  ['Label', 'Inline Composing'])
    assert_tokens(xpp.list_attr,
                  '<LimitRange> { "false" "true" "astring" 2.3 4 <hi> "ho"}',
                  ['LimitRange',
                   [False, True, "astring", 2.3, 4, ('hi', 'ho')]])
    # A section is some attrs
    assert_tokens(xpp.attr_section,
                  """<Label> "Inline Composing" 
                  <Tooltip> "Invokes Inline Composing." 
                  <LimitRange> { "false" "true" }""",
                  ['Label', 'Inline Composing',
                   'Tooltip', "Invokes Inline Composing.",
                   'LimitRange', False, True])
