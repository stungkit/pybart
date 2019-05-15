import sys
import chardet

import conllu_wrapper as cw
import converter


def main_internal(sentences_text, out_as_raw_test=True):
    parsed, all_comments = cw.parse_conllu(sentences_text)
    converted = converter.convert(parsed)
    if out_as_raw_test:
        return cw.serialize_conllu(converted, all_comments)
    else:
        return converted


def main(sentences_path, out_path=None):
    # best effort: lets try the most trivial encoding, then, if not successful find the correct encoding.
    try:
        encoding = "utf8"
        with open(sentences_path, "r", encoding=encoding) as f:
            ready_to_write = main_internal(f.read())
    except UnicodeDecodeError:
        encoding = chardet.detect(open(sentences_path, 'rb').read())['encoding']
        with open(sentences_path, "r", encoding=encoding) as f:
            ready_to_write = main_internal(f.read())
    
    if out_path:
        with open(out_path, "w", encoding=encoding) as f:
            f.write(ready_to_write)
    else:
        return ready_to_write


def print_usage():
    print("Usage: main.py input_path [output_path]\n"
          "Both input and output should and would be in CoNLL-U format.")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        main(sys.argv[1])
    elif len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        print_usage()
