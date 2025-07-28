import json
import os
import pandas as pd

def main(database_path, string_path):
    # Step 1: Read all strings from the Excel file
    print(f"Reading strings from: {string_path}")
    try:
        df = pd.read_excel(string_path)
        # Assuming the strings are in the first column, adjust if needed
        strings_to_filter = set(df.iloc[:, 0].dropna().tolist())
        print(f"Found {len(strings_to_filter)} strings to filter")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    # Step 2: Read the JSON database
    print(f"Reading database from: {database_path}")
    try:
        with open(database_path, 'r', encoding='utf-8') as f:
            database = json.load(f)
        original_count = len(database)
        print(f"Original database has {original_count} entries")
    except Exception as e:
        print(f"Error reading database file: {e}")
        return

    # Step 3: Filter out entries where value[0] matches any string from the Excel file
    filtered_database = {}
    removed_count = 0
    
    for key, value in database.items():
        if value[0] not in strings_to_filter:
            filtered_database[key] = value
        else:
            removed_count += 1
    
    print(f"Removed {removed_count} entries from database")
    print(f"Filtered database has {len(filtered_database)} entries")

    # Step 4: Save the filtered result to a new JSON file
    base_name, ext = os.path.splitext(database_path)
    output_path = f"{base_name}_AprilFilter{ext}"
    
    print(f"Saving filtered database to: {output_path}")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_database, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved filtered database")
    except Exception as e:
        print(f"Error saving filtered database: {e}")

if __name__ == "__main__":
    database_folder = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v11\database"
    string_folder = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\0612_Source"
    path_list = [
        ('PDR_enu_esp_database.json', '0612_ESP_PDR_April.xlsx'),
        ('PHD_enu_esp_database.json', '0612_ESP_PHD_April.xlsx'),
        ('PDR_enu_ita_database.json', '0612_ITA_PDR_April.xlsx'),
        ('PHD_enu_ita_database.json', '0612_ITA_PHD_April.xlsx'),
        ('PDR_enu_fra_database.json', '0612_FRA_PDR_April.xlsx'),
        ('PHD_enu_fra_database.json', '0612_FRA_PHD_April.xlsx'),
    ]
    for path in path_list:
        database_path = os.path.join(database_folder, path[0])
        string_path = os.path.join(string_folder, path[1])
        print(f"Processing {database_path} with strings from {string_path}")
        main(database_path, string_path)
