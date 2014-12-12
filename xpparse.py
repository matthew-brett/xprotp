""" Pyparsing parser for Siemens xprotocol XML-like format
"""

from collections import OrderedDict

from pyparsing import (Regex, Suppress, OneOrMore, ZeroOrMore, Group, Optional,
                       Forward, SkipTo, CaselessLiteral, Dict, removeQuotes,
                       Each, Word, alphanums, nums, dblQuotedString, Literal)


# Character literals
LCURLY = Suppress('{')
RCURLY = Suppress('}')
DOT = Suppress('.')
LANGLE = Suppress('<')
RANGLE = Suppress('>')

quoted_oneline = dblQuotedString
quoted_multi = Regex(
    r'"(?:[^"]|(?:"")|(?:\\x[0-9a-fA-F]+)|(?:\\.))*"').setName(
        "string enclosed in double quotes").setParseAction(removeQuotes)
ascconv_block = Regex(r'### ASCCONV BEGIN ###$(.*?)^### ASCCONV END ###')


def make_literal_tag(tag_name):
    return LANGLE + CaselessLiteral(tag_name) + RANGLE


xprotocol_tag = make_literal_tag('xprotocol')
bare_tag = LANGLE + Word(alphanums) + RANGLE
int_num = Word(nums).setParseAction( lambda s,l,t: [ int(t[0]) ] )
float_num = Regex(
    r'[+-]?(?=\d*[.eE])(?=\.?\d)\d*\.?\d*(?:[eE][+-]?\d+)?').setParseAction(
    lambda s,l,t: [ float(t[0]) ])
true = Literal('"true"').setParseAction(lambda s,l,t: [ True ])
false = Literal('"false"').setParseAction(lambda s,l,t: [ False ])
bool_ = true | false
value = Forward() # value can include key_value, so recursive
key_value = (bare_tag + value).setParseAction(
    lambda s,l,t: [(t[0], t[1])])
value <<= bool_ | float_num | int_num | quoted_multi | key_value
# Return list value as list
list_value = (LCURLY + ZeroOrMore(value) + RCURLY).setParseAction(
    lambda s,l,t: [[v for v in t]])
bool_attr = bare_tag + bool_
float_attr = bare_tag + float_num
int_attr = bare_tag + int_num
string_attr = bare_tag + quoted_multi
list_attr = bare_tag + list_value
attrs = bool_attr | float_attr | int_attr | string_attr | list_attr
# Return attr_section as OrderedDict
attr_section = ZeroOrMore(attrs).setParseAction(
    lambda s,l,t: OrderedDict(t))


def make_named_tag(tag_type):
    return (LANGLE +
            CaselessLiteral(tag_type) +
            DOT +
            quoted_oneline.setName('tag_name') +
            RANGLE)


def make_named_block(tag_type, contents):
    return (make_named_tag(tag_type) + LCURLY + contents + RCURLY)


def make_param_block(tag_type, contents):
    return make_named_block(tag_type, attr_section + Optional(contents))


param_bool = make_param_block('parambool', bool_)
param_long = make_param_block('paramlong', int_num)
param_array = make_param_block('paramarray', list_value)
# Recursive definition of blocks, can includ param_map
param_block = Forward()
param_map = make_param_block('parammap', param_block)
# Now we can define block with param_map definition
param_block <<= (param_bool | param_long | param_array | param_map)
# Fancy functor and service stuff
event = make_named_block("event", list_value)
method = make_named_block("method", list_value)
connection = make_named_block("connection", list_value)
param_functor = make_named_block('paramfunctor',
                            make_literal_tag('class') +
                            ZeroOrMore(param_block) +
                            Each([event, method, connection]))
pipe_service = make_named_block('pipeservice',
                                make_literal_tag('class') +
                                OneOrMore(param_block | param_functor))
param_card_layout = make_named_block('paramcardlayout', attr_section)
dependency = make_named_block('dependency', list_value)

xprotocol = (xprotocol_tag +
             LCURLY +
             attr_section +
             ZeroOrMore(param_block) +
             RCURLY +
             Optional(ascconv_block))


if __name__ == '__main__':
    with open('xprotocol_sample.txt', 'rt') as fobj:
        contents = fobj.read()

    res = xprotocol.parseString(contents)
