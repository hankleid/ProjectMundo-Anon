from translation import Translator
from article import *
import tools
import os
import time

# doi = "10.1038/s41467-023-43444-3" # health
# doi = "10.1038/s41467-024-52834-0" # Hsu et al.
# doi = "10.1038/s41467-018-04608-8" # zou
# doi = "10.1038/s41467-023-42766-6" # cats
# doi = "10.1038/s41467-017-00516-5" # Ahn et al.
# doi = "10.1038/s41467-019-11343-1" # physics/EE
# doi = "10.1038/s41467-023-40666-3" # human behavior

# doi = "10.1038/s41598-023-44786-0" # Le (vie)
# doi = "10.1038/s41467-022-29976-0" # Scuri (ita)
# doi = "10.1038/s41467-019-14096-z" # Roques-Carmes (fra)
# doi = "10.1038/s41586-024-07386-0" # Choi (kor)
# doi = "10.1038/s41467-021-21624-3" # Gyger (deu)
# doi = "10.1038/s41746-019-0216-8" # Ghorbani (per)
# doi = "10.1038/s41467-023-44527-x" # Kim (kor)
# doi = "10.1038/s41586-023-05748-8" # Jo (kor)
# doi = "10.1038/s42005-020-00412-3" # Mayor (fra)
# doi = "10.1038/s41467-024-48975-x" # Guan (zh1)
# doi = "10.1038/srep35658" # Sayed (ben)
# doi = "10.1038/s41377-020-00354-z" # Lustig (heb)
# doi = "10.1038/s41598-022-23052-9" # Bianchi (ita)
# doi = "10.1038/s41467-024-52834-0" # Hsu (zh2)
# doi = "10.1103/PRXQuantum.3.040326" # Gonzales-Garcia (spa)
doi = "10.1038/s41467-024-50750-x" # Franco-Rubio (spa)

# doi = "10.1038/s41598-023-51013-3" # sci rep 2
# doi = "10.1038/s41598-023-43026-9" # sci rep 3
# doi = "10.1038/s41598-023-45072-9" # covid
# doi = "10.1038/s41467-023-43949-x" # quantum optics
# doi = "10.1038/s41467-023-43067-8" # drug delivery *
# doi = "10.1038/s41467-023-43963-z" # materials science *

# folder_path = filename_from_DOI(doi=doi)

# data = get_nature_article(doi)
data = get_nature_article(doi)

# f = open(f"index.xml", "w")
# f.write(data.prettify())
# f.close()

tl = Translator("gpt")
tl.use_context = True
languages = [l for l in load_langs()['translation'].keys()]#[-6:]
# languages = languages[languages.index("Vietnamese"):]
# languages = ["Chinese (simplified characters)","Bengali","Urdu","Marathi","Tamil","Telugu","Gujarati"]#, "Chinese (traditional characters)", "Japanese"]
languages = ["English", "Spanish"]

if tl.use_context:
    fulltext_dir = f"FullTexts/{filename_from_DOI(doi=doi)}"
    fulltext_path = f"{fulltext_dir}/eng_full.txt"
    if not os.path.isdir(fulltext_dir):
        os.mkdir(fulltext_dir)
    if not os.path.isfile(fulltext_path):
        save_fulltext(get_copy(data), f"FullTexts/{filename_from_DOI(doi=doi)}/eng_full.txt")
    
    tl.load_article(fulltext_path)
    print(tl.context)

t = time.time()
for lang in languages:
    print(lang)
    this_data = get_copy(data)

    if lang != "English":
        translate_article(this_data, tl, lang)
        print(f"{lang}: {tl.count_tokens()}")

    add_mathML(this_data)
    change_graphic_dir(this_data)

    # SAVING
    doi_name = filename_from_DOI(doi=doi)
    folder_path = f"articles/{doi_name}"
    if not os.path.isdir(folder_path):
        os.mkdir(folder_path)
    
    f = open(f"{folder_path}/{load_langs()['translation'][lang]}.xml", "w")
    f.write(this_data.prettify())
    f.close()

    # ADD THIS ARTICLE TO THE CATALOG.

    tl.reset()


t = time.time() - t
print(f"{len(languages)} language(s) took {round(t/60)} minutes.")

# Update catalog.
# tools.update_dropdown_langs(languages)

tools.update_catalog([doi_name])
tools.update_index_files(languages)