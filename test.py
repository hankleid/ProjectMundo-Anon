from article import *
from translation import Translator

# doi = filename_from_DOI(doi="10.1038/s41467-017-00516-5") # ahn
# doi = filename_from_DOI(doi="10.1038/s41467-019-11343-1") # Jelena
# doi = filename_from_DOI(doi="10X1038_s41467-023-42766-6") # cats
# doi = filename_from_DOI(doi="10.1038/s41467-023-43444-3") # health
# doi = filename_from_DOI(doi="10.1038/s41467-018-04608-8") # zou
# doi = filename_from_DOI(doi="10.1038/s41467-023-40666-3") # human behavior

doi = filename_from_DOI(doi="10.1038/s41467-024-50750-x") # franco-rubio (spa)

lang = "zh1"
# langs = [l for l in load_langs()['translation'].values()]#[-6:]
tl = Translator('gpt')
tl.use_context = True
tl.load_article(f'FullTexts/{doi}/eng_full.txt')
# langs = ["eng"]
xml = None
for l in ["spa"]:
    with open(f'articles/{doi}/{l}.xml', 'r') as f:
        xml = "".join(f.readlines())
        xml = BeautifulSoup(xml, features="xml")
        p = xml.body.find("p", {"id":"Par51"})
        t_p = tl.translate_xml(p, "Spanish")
        xml_t_p = BeautifulSoup(t_p, features="xml")
        print(xml_t_p.prettify())
        # xml = xml.find(xml.name)

    fd = f"FullTexts/{doi}/{l}_full.txt"
    print(fd)
    # save_fulltext(xml, fd)


# tl = Translator("gpt")
# tl.upload_images(doi=doi)

# ret = tl.chat_prompt_with_figures("Please describe these images.")
# print(ret)