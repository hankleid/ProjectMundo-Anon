from translation import *
from article import load_text, save_text, filename_from_DOI, load_langs
from QnA import make_fulltext
import time

def chunkify(txt):
    # splits the full text article into chunks to translate.
    chunks = []
    i = 0
    stopper = '\n\n'
    while i != -1 and i < len(txt):
        j = txt[i:].find(stopper)+i
        chunks.append(txt[i:j])
        i = j+len(stopper)
    return chunks

def translate(tl, txts, lang, prompt=None):
    # translates each txt in txts into lang.
    # returns the translated list of txts.

    if isinstance(tl, GoogleTranslator):
        _, res = tl.translate(txts, lang)
    elif isinstance(tl, Translator): # LLM
        res = tl.translate_text(txts, lang, prompt)
    else:
        return None
    return res

def save_chunks(txts, savepath, newfile=True):
    # writes each txt in txtx to savepath.
    # puts \n\n between each chunk.
    if newfile:
        save_text(savepath, '') # new file
    with open(savepath, 'a') as f:
        for txt in txts:
            f.write(txt+'\n\n')

if __name__ == "__main__":
    article2 = "10.1038/s41467-018-04608-8" # zou
    ahn = "10.1038/s41467-017-00516-5" # Ahn (kor)

    article10 = "10.1038/s41598-023-51013-3" # sci rep 2 **
    article11 = "10.1038/s41598-023-43026-9" # biochem, endochrinology, neuroscience **
    article12 = "10.1038/s41598-023-45072-9" # covid **
    article13 = "10.1038/s41467-023-43949-x" # quantum optics **
    article14 = "10.1038/s41467-023-43067-8" # drug delivery **
    article15 = "10.1038/s41467-023-43963-z" # materials science **

    # doi = "10.1038/s41586-024-07386-0" # Choi (kor)
    # doi = "10.1038/s41598-022-23052-9" # Bianchi (ita)
    # doi = "10.1038/s42005-020-00412-3" # Mayor (fra)
    # doi = "10.1038/s41746-019-0216-8" # Ghorbani (per)
    doi = "10.1038/s41377-020-00354-z" # Lustig (heb)

    articles = [filename_from_DOI(doi=d) for d in [article10,article11,article12,article13,article14,article15]]
    
    langs_dict = load_langs()['translation']
    langs = [l for l in langs_dict.keys()][1:]
    langs = ["Hebrew"]

    tl = Translator('gpt')
    tl.load_example()
    tl.use_example = True
    tl.temp = 0.5


    for a in [filename_from_DOI(doi=doi)]:#articles[3:4]:
        fd = f"FullTexts/{a}"
        # loadpath = f"{fd}/eng_full.txt"
        loadpath = f"{fd}/samples.txt"

        chunks = chunkify(load_text(loadpath))
        chunks = [chunks[0]+"\n\n"+chunks[1]]#+"\n\n"+chunks[2]]#+"\n\n"+chunks[3]]
        print(chunks)

        print(a)
        for lang in langs:
            # make_fulltext(doi, lang)

            prompt = f"In the following scientific excerpt, please take note of any highly domain specific words in this excerpt. Then, please translate the excerpt into {lang}. But do not translate those highly domain specific words that you identified. For those words, keep the original English words in your translation instead. Everything else in the excerpt should be translated into {lang}.\n\n"
            try:
                new_chunks = translate(tl, chunks, lang)#, prompt=prompt)
                print(new_chunks)
                save_chunks(new_chunks, savepath=loadpath, newfile=False)#f"{fd}/{langs_dict[lang]}_notech.txt")
                pass
            except Exception as e:
                print(a, lang)
                print(e)

            # time.sleep(1)
        


    # inputs, res = tl.translate(["hello!","goodbye!"],"Korean")
    # print(res)