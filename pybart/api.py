import math

from .conllu_wrapper import parse_conllu, serialize_conllu, parse_odin, conllu_to_odin, parsed_tacred_json
from .converter import convert, get_conversion_names as inner_get_conversion_names, init_conversions


def convert_bart_conllu(conllu_text, enhance_ud=True, enhanced_plus_plus=True, enhanced_extra=True, preserve_comments=False, conv_iterations=math.inf, remove_eud_info=False, remove_extra_info=False, remove_node_adding_conversions=False, remove_unc=False, query_mode=False, funcs_to_cancel=None, ud_version=1):
    parsed, all_comments = parse_conllu(conllu_text)
    converted, _ = convert(parsed, enhance_ud, enhanced_plus_plus, enhanced_extra, conv_iterations, remove_eud_info, remove_extra_info, remove_node_adding_conversions, remove_unc, query_mode, funcs_to_cancel, ud_version)
    return serialize_conllu(converted, all_comments, preserve_comments)


def _convert_bart_odin_sent(doc, enhance_ud, enhanced_plus_plus, enhanced_extra, conv_iterations, remove_eud_info, remove_extra_info, remove_node_adding_conversions, remove_unc, query_mode, funcs_to_cancel, ud_version):
    sents = parse_odin(doc)
    converted_sents, _ = convert(sents, enhance_ud, enhanced_plus_plus, enhanced_extra, conv_iterations, remove_eud_info, remove_extra_info, remove_node_adding_conversions, remove_unc, query_mode, funcs_to_cancel, ud_version)
    return conllu_to_odin(converted_sents, doc)


def convert_bart_odin(odin_json, enhance_ud=True, enhanced_plus_plus=True, enhanced_extra=True, conv_iterations=math.inf, remove_eud_info=False, remove_extra_info=False, remove_node_adding_conversions=False, remove_unc=False, query_mode=False, funcs_to_cancel=None, ud_version=1):
    if "documents" in odin_json:
        for doc_key, doc in odin_json["documents"].items():
            odin_json["documents"][doc_key] = _convert_bart_odin_sent(doc, enhance_ud, enhanced_plus_plus, enhanced_extra, conv_iterations, remove_eud_info, remove_extra_info, remove_node_adding_conversions, remove_unc, query_mode, funcs_to_cancel, ud_version)
    else:
        odin_json = _convert_bart_odin_sent(odin_json, enhance_ud, enhanced_plus_plus, enhanced_extra, conv_iterations, remove_eud_info, remove_extra_info, remove_node_adding_conversions, remove_unc, query_mode, funcs_to_cancel, ud_version)
    
    return odin_json


def convert_bart_tacred(tacred_json, enhance_ud=True, enhanced_plus_plus=True, enhanced_extra=True, conv_iterations=math.inf, remove_eud_info=False, remove_extra_info=False, remove_node_adding_conversions=False, remove_unc=False, query_mode=False, funcs_to_cancel=None, ud_version=1):
    sents = parsed_tacred_json(tacred_json)
    converted_sents, _ = convert(sents, enhance_ud, enhanced_plus_plus, enhanced_extra, conv_iterations, remove_eud_info, remove_extra_info, remove_node_adding_conversions, remove_unc, query_mode, funcs_to_cancel, ud_version)
    
    return converted_sents


def convert_spacy_doc(doc, enhance_ud=True, enhanced_plus_plus=True, enhanced_extra=True, conv_iterations=math.inf, remove_eud_info=False, remove_extra_info=False, remove_node_adding_conversions=False, remove_unc=False, query_mode=False, funcs_to_cancel=None, ud_version=1, one_time_initialized_conversions=None):
    from .spacy_wrapper import parse_spacy_sent, serialize_spacy_doc
    parsed_doc = [parse_spacy_sent(sent) for sent in doc.sents]
    converted, convs_done = convert(parsed_doc, enhance_ud, enhanced_plus_plus, enhanced_extra, conv_iterations, remove_eud_info, remove_extra_info, remove_node_adding_conversions, remove_unc, query_mode, funcs_to_cancel, ud_version, one_time_initialized_conversions)
    return serialize_spacy_doc(doc, converted), converted, convs_done


class Converter:
    def __init__(self, enhance_ud=True, enhanced_plus_plus=True, enhanced_extra=True, conv_iterations=math.inf, remove_eud_info=False, remove_extra_info=False, remove_node_adding_conversions=False, remove_unc=False, query_mode=False, funcs_to_cancel=None, ud_version=1):
        self.config = (enhance_ud, enhanced_plus_plus, enhanced_extra, conv_iterations, remove_eud_info, remove_extra_info, remove_node_adding_conversions, remove_unc, query_mode, funcs_to_cancel, ud_version)
        # make conversions and (more importantly) constraint initialization, a one timer.
        self.conversions = init_conversions(remove_node_adding_conversions, ud_version)
    
    def __call__(self, doc):
        serialized_spacy_doc, converted_sents, convs_done = convert_spacy_doc(doc, *self.config, self.conversions)
        self._converted_sents = converted_sents
        self._convs_done = convs_done
        return serialized_spacy_doc
    
    def get_converted_sents(self):
        return self._converted_sents
    
    def get_max_convs(self):
        return self._convs_done


def get_conversion_names():
    return inner_get_conversion_names()
