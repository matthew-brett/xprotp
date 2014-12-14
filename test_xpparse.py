""" Test module to parse xprotocl text
"""

import xpparse as xpp

from pyparsing import ParseException, Optional

from nose.tools import (assert_true, assert_false, assert_equal,
                        assert_not_equal, assert_raises)


def to_comparable(parse_results, expected):
    if hasattr(expected, 'keys'):
        out = {}
        for k, v in parse_results.items():
            out[k] = to_comparable(v, expected[k])
        return out
    elif isinstance(expected, list):
        out = []
        assert_equal(len(parse_results), len(expected))
        for v, ex_v in zip(parse_results, expected):
            out.append(to_comparable(v, ex_v))
        return out
    return parse_results


def assert_tokens(pattern, source, expected):
    assert_equal(
        to_comparable(pattern.parseString(source, True), expected),
        expected)


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
    # Key value returns list, with converted values
    assert_tokens(xpp.key_value, '<thing> "true" ', [['thing', True]])
    assert_tokens(xpp.key_value, '<other> "string" ', [['other', "string"]])
    assert_tokens(xpp.key_value, '< some> 2.3 ', [['some', 2.3]])
    # Lists can contain any of the above
    assert_tokens(xpp.list_value,
                  '{ "false" "true" 1 "three" }',
                  [[False, True, 1, "three"]])
    assert_tokens(xpp.list_value,
                  '{ "false" "true" 1 "three" }',
                  [[False, True, 1, "three"]])
    assert_tokens(xpp.list_value,
                  '{ "false" "true" <here> "there" 3 10.4 }',
                  [[False, True, ['here', 'there'], 3, 10.4]])
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
                   [False, True, "astring", 2.3, 4, ['hi', 'ho']]])
    # attr is any attr
    assert_tokens(xpp.attr,
                  '<Label> "Inline Composing"',
                  [['Label', 'Inline Composing']])
    assert_tokens(xpp.attr,
                  '<name> 2',
                  [['name', 2]])
    assert_tokens(xpp.attr,
                  '<LimitRange> { "false" "true" "astring" 2.3 4 <hi> "ho"}',
                  [['LimitRange',
                   [False, True, "astring", 2.3, 4, ['hi', 'ho']]]])
    # A section is some attrs
    assert_tokens(xpp.attrs,
                  """<Label> "Inline Composing"
                  <Tooltip> "Invokes Inline Composing."
                  <LimitRange> { "false" "true" }""",
                  dict(attrs=
                       dict([('Label', 'Inline Composing'),
                             ('Tooltip', "Invokes Inline Composing."),
                             ('LimitRange', [False, True])])))


def test_param_tags():
    # Test parsing of tags for parameter blocks
    param_long_tag = xpp.make_named_tag('paramlong')
    assert_tokens(param_long_tag,
                  ' <ParamLong."Count"> ',
                  dict(tag_type='paramlong', tag_name='Count'))
    param_bool_tag = xpp.make_named_tag('parambool')
    assert_tokens(param_bool_tag,
                  '<ParamBool."IsInlineComposed">',
                  dict(tag_type='parambool', tag_name='IsInlineComposed'))
    param_map_tag = xpp.make_named_tag('parammap')
    assert_tokens(param_map_tag,
                  '<ParamMap."">',
                  dict(tag_type='parammap'))


def test_param_blocks():
    # Test parameter blocks
    assert_tokens(xpp.param_block,
                  """<ParamBool."IsInlineComposed">
                  {
                  <LimitRange> { "false" "true" }
                 }
                  """,
                  dict(tag_type='parambool',
                       tag_name='IsInlineComposed',
                       attrs=dict(LimitRange=[False, True])))
    assert_tokens(xpp.param_block,
                  """ <ParamLong."Count">
                  {
                  1
                 }""",
                  dict(tag_type='paramlong',
                       tag_name='Count',
                       attrs={},
                       value=1))
    assert_tokens(xpp.param_string,
      '<ParamString."GROUP">  { "Calculation"  }',
                  dict(tag_type='paramstring',
                       tag_name='GROUP',
                       attrs={},
                       value='Calculation'))


def test_param_array():
    assert_tokens(xpp.param_array,
                  """<ParamArray."EstimatedDuration">
                  {
                  <MinSize> 1
                  <MaxSize> 1000000000
                  <Default> <ParamLong."">
                  {
                 }
                  { 450 200 }
                 }""",
                  dict(tag_type='paramarray',
                       tag_name='EstimatedDuration',
                       attrs=dict(MinSize=1,
                                  MaxSize=1000000000),
                       default=dict(tag_type='paramlong',
                                    attrs={}),
                       value=[450, 200]))
    assert_tokens(xpp.param_array,
                  """
                  <ParamArray."BValue">
                  {
                  <Default> <ParamLong."">
                  {
                 }
                  { }
                 }""",
                  dict(tag_type='paramarray',
                       tag_name='BValue',
                       attrs={},
                       default=dict(tag_type='paramlong',
                                    attrs={}),
                       value=[]))


def test_param_map():
    assert_tokens(xpp.param_map,
                  """<ParamMap."">
                  {

                  <ParamBool."IsInlineComposed">
                  {
                  <LimitRange> { "false" "true" }
                 }

                  <ParamLong."Count">
                  {
                  1
                 }
                 }""",
                  dict(tag_type='parammap',
                       attrs={},
                       value=[dict(tag_type='parambool',
                                   tag_name='IsInlineComposed',
                                   attrs=dict(LimitRange=[False, True])),
                              dict(tag_type='paramlong',
                                   tag_name='Count',
                                   attrs={},
                                   value=1)]))


def test_event():
    assert_tokens(xpp.event,
                  '<Event."ImageReady">  { "int32_t" "class IceAs &" '
                  '"class MrPtr<class MiniHeader,class Parc::Component> &" '
                  '"class ImageControl &" }',
                  dict(tag_type='event',
                        tag_name='ImageReady',
                        value = ["int32_t",
                                 "class IceAs &",
                                 "class MrPtr<class MiniHeader,"
                                 "class Parc::Component> &",
                                 "class ImageControl &"]))


def test_method():
    assert_tokens(xpp.method,
                  '<Method."ComputeImage">  { "int32_t" "class IceAs &" '
                  '"class MrPtr<class MiniHeader,class Parc::Component> &" '
                  '"class ImageControl &"  }',
                  dict(tag_type='method',
                       tag_name='ComputeImage',
                       value = ["int32_t",
                                "class IceAs &",
                                "class MrPtr<class MiniHeader,"
                                "class Parc::Component> &",
                                "class ImageControl &"]))


def test_connection():
    assert_tokens(xpp.connection,
                  '<Connection."c1">  { '
                  '"ImageReady" '
                  '"DtiIcePostProcMosaicDecorator" '
                  '"ComputeImage"  }',
                  dict(tag_type='connection',
                        tag_name='c1',
                        value = ["ImageReady",
                                 "DtiIcePostProcMosaicDecorator",
                                 "ComputeImage"]))
    assert_tokens(xpp.connection,
                  '<Connection."c1">  { "ImageReady" "" "ComputeImage"  }',
                  dict(tag_type='connection',
                       tag_name='c1',
                       value = ["ImageReady",
                                "",
                                "ComputeImage"]))


def test_class():
    assert_tokens(xpp.class_,
                  '<Class> "MosaicUnwrapper@IceImagePostProcFunctors"',
                  {'class': "MosaicUnwrapper@IceImagePostProcFunctors"})


def test_emc():
    assert_tokens(xpp.emc,
"""
<Event."ImageReady">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
<Method."ComputeImage">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
<Connection."c1">  { "ImageReady" "DtiIcePostProcMosaicDecorator" "ComputeImage"  } """,
                    {'event': dict(
                        tag_type='event',
                        tag_name='ImageReady',
                        value = ["int32_t",
                                 "class IceAs &",
                                 "class MrPtr<class MiniHeader,"
                                 "class Parc::Component> &",
                                 "class ImageControl &"]),
                    'method': dict(
                        tag_type='method',
                        tag_name='ComputeImage',
                        value = ["int32_t",
                                 "class IceAs &",
                                 "class MrPtr<class MiniHeader,"
                                 "class Parc::Component> &",
                                 "class ImageControl &"]),
                    'connection': dict(
                        tag_type='connection',
                        tag_name='c1',
                        value = ["ImageReady",
                                 "DtiIcePostProcMosaicDecorator",
                                 "ComputeImage"])})


def test_functor():
    assert_tokens(xpp.param_functor,
"""
<ParamFunctor."MosaicUnwrapper">
{
<Class> "MosaicUnwrapper@IceImagePostProcFunctors"

<ParamBool."EXECUTE">  { }
<Event."ImageReady">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
<Method."ComputeImage">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
<Connection."c1">  { "ImageReady" "DtiIcePostProcMosaicDecorator" "ComputeImage"  }
}""",
                  {'tag_type': 'paramfunctor',
                   'tag_name': 'MosaicUnwrapper',
                   'class': "MosaicUnwrapper@IceImagePostProcFunctors",
                   'value': [dict(tag_type='parambool',
                                  tag_name='EXECUTE',
                                  attrs={})],
                   'event': dict(
                       tag_type='event',
                       tag_name='ImageReady',
                       value = ["int32_t",
                                "class IceAs &",
                                "class MrPtr<class MiniHeader,"
                                "class Parc::Component> &",
                                "class ImageControl &"]),
                   'method': dict(
                       tag_type='method',
                       tag_name='ComputeImage',
                       value = ["int32_t",
                                "class IceAs &",
                                "class MrPtr<class MiniHeader,"
                                "class Parc::Component> &",
                                "class ImageControl &"]),
                   'connection': dict(
                       tag_type='connection',
                       tag_name='c1',
                       value = ["ImageReady",
                                "DtiIcePostProcMosaicDecorator",
                                "ComputeImage"])})


def test_pipe_service():
    xpp.pipe_service.parseString(
        """
    <PipeService."EVA">
    {
      <Class> "PipeLinkService@MrParc"

      <ParamLong."POOLTHREADS">  { 1  }
      <ParamString."GROUP">  { "Calculation"  }
      <ParamLong."DATATHREADS">  { }
      <ParamLong."WATERMARK">  { 16  }
      <ParamString."tdefaultEVAProt">  { "%SiemensEvaDefProt%/DTI/DTI.evp"  }
      <ParamFunctor."MosaicUnwrapper"> 
      {
        <Class> "MosaicUnwrapper@IceImagePostProcFunctors" 

        <ParamBool."EXECUTE">  { }
        <Event."ImageReady">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
        <Method."ComputeImage">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
        <Connection."c1">  { "ImageReady" "" "ComputeImage"  }
      }
      <ParamFunctor."DtiIcePostProcFunctor"> 
      {
        <Class> "DtiIcePostProcFunctor@DtiIcePostProc" 

        <ParamBool."EXECUTE">  { "true"  }
        <ParamArray."BValue"> 
        {
          <Default> <ParamLong.""> 
          {
          }
          { }

        }
        <ParamLong."Threshold">  { 40  }
        <ParamLong."NoOfDirections4FirstBValue">  { }
        <ParamLong."ScalingFactor">  { 1  }
        <ParamLong."UpperBound">  { }
        <ParamLong."Threshold4AutoLoadInViewer">  { 400  }
        <ParamLong."DiffusionMode">  { }
        <ParamBool."DiffWeightedImage">  { "true"  }
        <ParamBool."ADCMap">  { }
        <ParamBool."AverageADCMap">  { "true"  }
        <ParamBool."TraceWeightedImage">  { "true"  }
        <ParamBool."FAMap">  { "true"  }
        <ParamBool."Anisotropy">  { }
        <ParamBool."Tensor">  { }
        <ParamBool."E1">  { }
        <ParamBool."E2">  { }
        <ParamBool."E3">  { }
        <ParamBool."E1-E2">  { }
        <ParamBool."E1-E3">  { }
        <ParamBool."E2-E3">  { }
        <ParamBool."VR">  { }
        <ParamLong."bValueforADC">  { }
        <ParamBool."bValueforADCCheckbox">  { }
        <ParamBool."InvertGrayScale">  { }
        <ParamBool."ExponentialADCMap">  { "true"  }
        <ParamBool."CalculatedImage">  { }
        <ParamLong."CalculatedbValue">  { 1400  }
        <ParamBool."RA">  { }
        <ParamBool."Linear">  { }
        <ParamBool."Planar">  { }
        <ParamBool."Spherical">  { }
        <ParamBool."IsInlineProcessing">  { "true"  }
        <Method."ComputeImage">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
        <Event."ImageReady">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
        <Connection."c1">  { "ImageReady" "DtiIcePostProcMosaicDecorator" "ComputeImage"  }
      }
      <ParamFunctor."DtiIcePostProcMosaicDecorator"> 
      {
        <Class> "DtiIcePostProcMosaicDecorator@DtiIcePostProc" 
        
        <ParamBool."EXECUTE">  { "true"  }
        <ParamBool."Mosaic">  { "true"  }
        <ParamBool."MosaicDiffusionMaps">  { }
        <Event."ImageReady">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
        <Method."ComputeImage">  { "int32_t" "class IceAs &" "class MrPtr<class MiniHeader,class Parc::Component> &" "class ImageControl &"  }
        <Connection."connection0">  { "ImageReady" "imagesend_ps.imagesend" "ComputeImage"  }
      }
      <ParamBool."WIPFlagSetbySequenceDeveloper">  { }
    }""")


def test_dependency():
    assert_tokens(xpp.dependency,
                  """
                  <Dependency."MrMS_DH_TpPosMode"> {"MultiStep.TpPosMode"
                  <Dll> "MrMultiStepDependencies" <Context> "ONLINE" }
                  """,
                  dict(tag_type='dependency',
                       tag_name="MrMS_DH_TpPosMode",
                       value=["MultiStep.TpPosMode",
                              ['Dll', "MrMultiStepDependencies"],
                              ['Context', "ONLINE"]]))


def test_param_card_layout():
    assert_tokens(xpp.param_card_layout,
"""<ParamCardLayout."Multistep">
  {
    <Repr> "LAYOUT_10X2_WIDE_CONTROLS"
    <Control>  { <Param> "MultiStep.IsMultistep" <Pos> 110 3 <Repr> "UI_CHECKBOX" }
    <Control>  { <Param> "MultiStep.SubStep" <Pos> 77 18 }
    <Line>  { 126 3 126 33 }
    <Line>  { 276 48 276 140 }
  }""",
                  dict(tag_type='paramcardlayout',
                       tag_name="Multistep",
                       value=[['Repr', "LAYOUT_10X2_WIDE_CONTROLS"],
                              ['Control',
                               [['Param', "MultiStep.IsMultistep"],
                                'Pos', 110, 3, 'Repr', "UI_CHECKBOX"]],
                              ['Control',
                               ['Param', "MultiStep.SubStep", 'Pos', 77, 18]],
                              ['Line',  [ 126, 3, 126, 33 ]],
                              ['Line',  [ 276, 48, 276, 140 ]]]))


def test_eva_string_table():
    assert_tokens(xpp.list_attr, """
  <EVAStringTable>
  {
    34
    400 "Multistep Protocol"
    401 "Step"
    447 "Adaptive"
  }""",
                  ['EVAStringTable',
                   [34,
                    400, "Multistep Protocol",
                    401, "Step",
                    447, "Adaptive"]])
