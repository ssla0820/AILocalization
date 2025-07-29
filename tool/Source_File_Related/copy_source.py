import os
import shutil

def main(file_list, save_path, language_list):
    for file in file_list:
        for lang in language_list:
            file_name = os.path.basename(file)

            base_name, extension = os.path.splitext(file_name)
            new_file_name = f"{base_name}_{lang}{extension}"

            new_file_path = os.path.join(save_path, new_file_name)
            shutil.copy(file, new_file_path)
            print(f"Copied {file} to {new_file_path}")


if __name__ == "__main__":
    file_path = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\0728_Source"
    save_path = r"E:\Debby\9_Scripts\TranslateHTML\Translate_HTML_XML_v8\Report\0728_Source"

    file_list = [os.path.join(file_path, file) for file in os.listdir(file_path)]
    language_list = ['FRA', 'KOR', 'ITA', 'ESP']

    main(file_list, save_path, language_list)


