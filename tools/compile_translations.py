"""Build the Django English catalog from translations.json without GNU gettext.

The source catalog contains singular messages only (including interpolated
sentences). Django's built-in catalogs supply standard validation messages.
"""
import json
import struct
from pathlib import Path


def compile_catalog():
    directory = Path(__file__).resolve().parent.parent / 'locale' / 'en'
    translations = json.loads((directory / 'translations.json').read_text(encoding='utf-8'))
    translations[''] = (
        'Project-Id-Version: wedding\nLanguage: en\nMIME-Version: 1.0\n'
        'Content-Type: text/plain; charset=UTF-8\nContent-Transfer-Encoding: 8bit\n'
        'Plural-Forms: nplurals=2; plural=(n != 1);\n'
    )
    messages = sorted(translations.items())
    destination = directory / 'LC_MESSAGES'
    destination.mkdir(parents=True, exist_ok=True)
    po = '\n\n'.join(f'msgid {json.dumps(key, ensure_ascii=False)}\nmsgstr {json.dumps(value, ensure_ascii=False)}' for key, value in messages)
    (destination / 'django.po').write_text(po + '\n', encoding='utf-8')
    count = len(messages)
    ids = [key.encode('utf-8') for key, _ in messages]
    values = [value.encode('utf-8') for _, value in messages]
    start = 28 + 16 * count
    original_data = b'\0'.join(ids) + b'\0'
    translated_data = b'\0'.join(values) + b'\0'
    def offsets(strings, offset):
        table = b''
        for string in strings:
            table += struct.pack('<2I', len(string), offset)
            offset += len(string) + 1
        return table
    header = struct.pack('<7I', 0x950412de, 0, count, 28, 28 + 8 * count, 0, 0)
    (destination / 'django.mo').write_bytes(
        header + offsets(ids, start) + offsets(values, start + len(original_data))
        + original_data + translated_data
    )
    print(f'Compiled {count - 1} English translations.')


if __name__ == '__main__':
    compile_catalog()
