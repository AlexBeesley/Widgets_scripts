import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
# Load environment variables from .env file
load_dotenv()

def transform_files():
    config_dir = os.getenv('CONFIG_DIR')
    
    # Create the transformed folder if it doesn't exist
    if not os.path.exists('transformed'):
        os.mkdir('transformed') 
        print("Created 'transformed' folder")

    # Copy all .config files to the transformed folder using multithreading
    with ThreadPoolExecutor() as executor:
        for filename in os.listdir(config_dir):
            if filename.endswith('.config'):
                executor.submit(shutil.copy, os.path.join(config_dir, filename), 'transformed')
                print(f"Copied {filename} to 'transformed' folder")

    # Loop through copied files and update XML using multithreading
    with ThreadPoolExecutor() as executor:
        for filename in os.listdir('transformed'):
            if filename.endswith('.config'):
                executor.submit(update_xml, filename)
    
def update_xml(filename):
    tree = ET.parse(os.path.join('transformed', filename))
    root = tree.getroot()
    
    for sidebarwidget in root.iter('sidebarwidgets'):
        for widget in sidebarwidget:
            key = widget.get('key')
            widget.text = '"umb://document/%s"' % key
            print(f"Updated widget with key: {key}")
            
    tree.write(os.path.join('transformed', filename))
    print(f"Updated XML in {filename}")

transform_files()
