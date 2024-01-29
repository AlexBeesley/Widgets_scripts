import json
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import tostring
import xml.dom.minidom as minidom
import re
import shutil
import os
from dotenv import dotenv_values


def load_lookup_dict():
    lookup_dict = {}
    with open('dict.txt', 'r', encoding='utf-8') as f:
        for line in f:
            key, value = line.strip().split(' : ')
            lookup_dict[key.lower()] = value
    return lookup_dict


def parse_json_from_cdata(cdata_text):
    json_text = re.sub(r'^<!\[CDATA\[\s*|\s*\]\]>$', '', cdata_text)
    return json.loads(json_text)


def get_widget_guids(value, lookup_dict, filename):
    if not all(isinstance(widget, dict) for widget in value):
        print(f"Unexpected type in value. Expected a list of dictionaries.")
        return
    for widget in value:
        label = widget.get('label')
        key = widget.get('key')
        guid = lookup_dict.get(label.lower())
        if guid:
            guid = guid.replace('-', '')
            guid = f"umb://document/{guid}"
            print(f"Updated widget with key: {key} to guid: {guid} for label: {label} in {filename}")
            yield guid


def format_xml_string(xml_string):
    replacements = {
        "&lt;": "<",
        "&gt;": ">",
        "&quot;": "\"",
        "&amp;": "&",
        "<Value>": "<Value><![CDATA[",
        "</Value>": "]]></Value>",
        "<Value/>": "<Value><![CDATA[]]></Value>",
        "<?xml version=\"1.0\" ?>": "<?xml version=\"1.0\" encoding=\"utf-8\"?>"
    }
    xml_string = re.sub(r'<!\[CDATA\[\s*|\s*\]\]>', '', xml_string)
    xml_string = "\n".join(line for line in xml_string.split("\n") if line.strip())
    for old, new in replacements.items():
        xml_string = xml_string.replace(old, new)
    return xml_string


def write_xml_to_file(xml_string, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        f.truncate(0)
        f.write(xml_string)


def copy_config_files():
    env_values = dotenv_values('.env')
    target_dir = env_values.get('CONFIG_DIR')
    if target_dir:
        config_files = [f for f in os.listdir(target_dir) if f.endswith('.config')]
        output_dir = os.path.join(os.getcwd(), 'output')
        os.makedirs(output_dir, exist_ok=True)
        for file in config_files:
            shutil.copy(os.path.join(target_dir, file), os.path.join(output_dir, file))
            print(f"Copied {file} to the 'output' folder.")
    else:
        print("TARGET_DIR not found in .env file.")


def main():
    copy_config_files()
    lookup_dict = load_lookup_dict()
    output_dir = os.path.join(os.getcwd(), 'output')
    for file in os.listdir(output_dir):
        if file.endswith('.config'):
            file_path = os.path.join(output_dir, file)
            tree = ET.parse(file_path)
            root = tree.getroot()
            value_tag = root.find('.//sidebarWidgets/Value')
            if value_tag is None:
                continue
            cdata_text = value_tag.text
            if cdata_text is None:
                continue
            value = parse_json_from_cdata(cdata_text)
            guids = list(get_widget_guids(value, lookup_dict, file))
            value_tag.text = json.dumps(guids, indent=2)
            xml_string = minidom.parseString(tostring(root)).toprettyxml(indent="  ")
            xml_string = format_xml_string(xml_string)
            write_xml_to_file(xml_string, file_path)


if __name__ == "__main__":
    main()
