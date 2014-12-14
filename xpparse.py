""" Pyparsing parser for Siemens xprotocol XML-like format
"""
from __future__ import print_function

from pyparsing import (Regex, Suppress, OneOrMore, ZeroOrMore, Group, Optional,
                       Forward, CaselessLiteral, Dict, removeQuotes,
                       Each, Word, alphanums, nums, dblQuotedString, Literal,
                       dictOf)


# Character literals
LCURLY = Suppress('{')
RCURLY = Suppress('}')
DOT = Suppress('.')
LANGLE = Suppress('<')
RANGLE = Suppress('>')

def _spa(element, action):
    """ Shortcut to set parse action """
    return element.setParseAction(action)


quoted_oneline = dblQuotedString
quoted_multi = _spa(Regex(r'"(?:[^"]|(?:"")|(?:\\x[0-9a-fA-F]+)|(?:\\.))*"'),
                    removeQuotes)
ascconv_block = Regex(r'### ASCCONV BEGIN ###$(.*?)^### ASCCONV END ###')


def make_literal_tag(tag_name):
    return LANGLE + CaselessLiteral(tag_name) + RANGLE


xprotocol_tag = make_literal_tag('xprotocol')
bare_tag = LANGLE + Word(alphanums) + RANGLE
int_num = _spa(Word(nums), lambda s,l,t: [ int(t[0]) ] )
float_num = _spa(Regex(
    r'[+-]?(?=\d*[.eE])(?=\.?\d)\d*\.?\d*(?:[eE][+-]?\d+)?'),
    lambda s,l,t: [ float(t[0]) ])
true = _spa(Literal('"true"'), lambda s,l,t: [ True ])
false = _spa(Literal('"false"'), lambda s,l,t: [ False ])
bool_ = true | false
simple_value = bool_ | float_num | int_num | quoted_multi
key_values = Group(bare_tag + OneOrMore(simple_value))
keys_values = Dict(ZeroOrMore(key_values))
list_entries = Group(ZeroOrMore(simple_value))('args') + keys_values('kwargs')
# Return list value as list
list_value = LCURLY + list_entries + RCURLY
bool_attr = bare_tag + bool_
float_attr = bare_tag + float_num
int_attr = bare_tag + int_num
string_attr = bare_tag + quoted_multi
list_attr = bare_tag + list_value
attr = Group(bool_attr | float_attr | int_attr | string_attr | list_attr)
attrs = Dict(ZeroOrMore(attr))('attrs')


def make_named_tag(tag_type):
    return (LANGLE +
            CaselessLiteral(tag_type)('tag_type') +
            DOT +
            _spa(quoted_oneline, removeQuotes)('tag_name') +
            RANGLE)


def make_named_block(tag_type, contents=None, pre=None, post=None):
    definition = make_named_tag(tag_type) + LCURLY
    if pre is not None:
        definition = definition + pre
    definition = definition + contents('value')
    if post is not None:
        definition = definition + post
    return definition + RCURLY


def make_param_block(tag_type, contents):
    return make_named_block(tag_type, pre=attrs, contents=contents)


param_bool = make_param_block('parambool', Optional(bool_))
param_long = make_param_block('paramlong', Optional(int_num))
param_string = make_param_block('paramstring', Optional(quoted_multi))
# Recursive definition of blocks, can include param_map
param_block = Forward()
array_default = dictOf(make_literal_tag('default'), param_block)
param_array = make_named_block('paramarray',
                               pre=attrs + array_default,
                               contents=_spa(Optional(list_value),
                                             lambda s, l, t: [t[0]]))
param_map = make_param_block('parammap', ZeroOrMore(Group(param_block)))
# Now we can define block with param_map definition
param_block <<= (param_bool |
                 param_long |
                 param_string |
                 param_array |
                 param_map)


# Fancy functor and service stuff
def make_args_block(tag_type):
    return (make_named_tag(tag_type) +
            LCURLY +
            list_entries +
            RCURLY)


event = make_args_block("event")
method = make_args_block("method")
connection = make_args_block("connection")
class_ = dictOf(make_literal_tag('class'), quoted_oneline)
emc = Each([Group(event)('event'),
            Group(method)('method'),
            Group(connection)('connection')])
param_functor = make_named_block('paramfunctor',
                                 pre=class_,
                                 contents=ZeroOrMore(Group(param_block)),
                                 post=emc)
pipe_service = make_named_block('pipeservice',
                                pre=class_,
                                contents=OneOrMore(Group(
                                    param_block | param_functor)))

param_card_layout = make_named_block('paramcardlayout',
                                     ZeroOrMore(attr))
dependency = make_args_block('dependency')

xprotocol = (xprotocol_tag +
             LCURLY +
             attrs +
             ZeroOrMore(param_block) +
             RCURLY +
             Optional(ascconv_block))


if __name__ == '__main__':
    with open('xprotocol_sample.txt', 'rt') as fobj:
        contents = fobj.read()
    res = xprotocol.parseString(contents, True)
    extras = []
    for v in res.value:
        if not v.tag_name.startswith('Protocol'):
            continue
        proto_str = v.value.replace('""', '"')
        extras.append(xprotocol.parseString(proto_str), True)
