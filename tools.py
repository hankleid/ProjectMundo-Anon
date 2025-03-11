from article import *
import os
import json



def update_catalog(dois):
    #
    # RE-RUN WHENEVER NEW ARTICLES ARE ADDED.
    #
    articles_dict = load_articles()
    # dois = [lang_dict["translation"][l] for a in articles]

    for doi in dois:
        print(doi)

        # get all available article titles and dois
        langs = [file for file in os.listdir(f"articles/{doi}") if file[-len(".xml"):] == ".xml"]
        
        if doi not in articles_dict.keys():
            articles_dict[doi] = {"langs":{}}

        for i in range(len(langs)):
            if langs[i][:-len(".xml")] == langs[i][0:3]: # format HAS to be exactly [lang].xml to be displayed on the website.
                with open(f"articles/{doi}/{str(langs[i])}", "r") as f:
                    code = langs[i][0:3]
                    this_data = BeautifulSoup(str(f.read()), features="xml")
                    if code == "eng":
                        date = this_data.find("pub-date", {"publication-format":"electronic"})
                        contribs = this_data.find("contrib-group").find_all("contrib", {"contrib-type":"author"})
                        articles_dict[doi]["meta"] = {
                            "journal": str_strip(this_data.find("abbrev-journal-title").string),
                            "volume": str_strip(this_data.find("volume").string),
                            # "pages": str_strip(this_data.find("fpage").string)+"-"+str_strip(this_data.find("lpage").string),
                            "doi": str_strip(this_data.find("article-id", {"pub-id-type":"doi"}).string),
                            "date": str_strip(date.find("year").string)+"-"+str_strip(date.find("month").string)+"-"+str_strip(date.find("day").string),
                            "authors": "".join([str_strip(c.find("given-names").string)+" "+str_strip(c.find("surname").string)+", " for c in contribs])[:-2]
                        }
                    title = str_strip(this_data.find("article-title").string)
                    articles_dict[doi]["langs"][code] = title

    with open("articles.json", "w+") as f:
        json.dump(articles_dict, f, ensure_ascii=False, indent=2)


def update_dropdown_langs(langs):
    # ***DEPRECATED***
    # POPULATE DROPDOWN LIST W/ ALL AVAILABLE LANGS
    # (links are blank -- they get populated by js/webscript.js)
    #
    html = BeautifulSoup(str(open("style/navigation.html").read()), features="html.parser")
    dropdown = html.find("div", {"id": "lang-dropdown"})
    dropdown.clear()
    
    lang_dict = load_langs()
    codes = [lang_dict["translation"][l] for l in langs]
    for code in codes:
        dropdown.append(BeautifulSoup(f"<a href='' id='{code}'>{lang_dict['codes'][code]}</a>", features="html.parser"))
    
    with open("style/navigation.html", "w+") as f:
        f.write(html.prettify())

def date_score(date):
    # format: YYYY/(M)M/(D)D
    i = date.find("-")
    sum = int(date[0:i]) * 10000
    j = date[i+1:].find("-")
    sum += int(date[i+1:i+1+j])*100 + int(date[-2:])
    return sum

def update_index_files(langs):
    #
    # CREATES NEW INDEX FILE FOR EACH LANGUAGE W/ TRANSLATED TITLES.
    # (currently uses the Korean index as the model)
    #
    html = BeautifulSoup(str(open("index/kor.html").read()), features="html.parser")
    articles = html.find("div", {"class": "articles-index"})
    scripts = [s for s in html.find_all("script")]

    lang_dict = load_langs()
    codes = [lang_dict["translation"][l] for l in langs]
    articles_dict = load_articles()
    dois = list(articles_dict.keys())

    _articles = []
    for code in codes:
        # Add links to all available articles.
        articles.clear()
        articles_with_lang = [doi for doi in dois if code in articles_dict[doi]['langs'].keys()]
        for a in articles_with_lang:
            m = articles_dict[a]["meta"]
            line1 = f"<div class='line1'><i>{m['journal']}</i> <b>{m['volume']}</b>, ({m['date'][0:4]})</div>"
            # line2 = f"<div class='line2'>DOI: {m['doi']}</div>"
            line2 = f"<div class='line2'>{m['authors']}</div>"

            html_str = f"<div class='index-entry'><div class='entry-link'><a href='/ProjectMundo-Anon-106A/articles/{a}/{code}.xml'>{articles_dict[a]['langs'][code]}</a></div><div class='entry-meta'>{line1}{line2}</div></div>"

            _articles.append({date_score(m['date']): BeautifulSoup(html_str, features="html.parser")})
        
        _articles = sorted(_articles, key=lambda d: -list(d.keys())[0])
        for a in _articles:
            articles.append(list(a.values())[0])
        
        # Change the on-load script.
        script = scripts[-1]
        script.clear()
        script.append(BeautifulSoup("setTimeout(function() {configureDropdown('index', '"+code+"');}, 100);", features="html.parser"))

        with open(f"index/{code}.html", "w+") as f:
            f.write(html.prettify())

if __name__ == "__main__":
    all_articles = [doi for doi in os.listdir(f"articles") if doi != ".DS_Store"]
    all_langs = [lang for lang in load_langs()['translation'].keys()]

    articles = all_articles
    # update_catalog(["10X1103_PRXQuantumX3X040326"])
    langs = all_langs
    # update_index_files(langs)

    count = 0
    for d in all_articles:
        for l in list(load_langs()['translation'].values())[1:]:
            path = f"articles/{d}/{l}.xml"
            if os.path.exists(path):
                count += 1
                # data = None
                # with open(path, "r") as f:
                #     data = BeautifulSoup(str(f.read()), features="xml")

                # # new_xsl_el = BeautifulSoup(f"<?xml-stylesheet type='text/xsl' href='/ProjectMundo-Anon-106A/style/jats-html.xsl'?>", features="xml")
                # # data.contents[0].replace_with(new_xsl_el)
                # change_graphic_dir(data)
                print(d, l)

                # with open(path, "w") as f:
                #     f.write(data.prettify())
    print(count)

    # title = this_data.find("article-title").string
    # print(title)

    # # add_mathML(this_data)
    # change_graphic_dir(this_data)

    # # SAVING
    # fn = filename_from_DOI(doi=doi)
    # f = open(path, "w+")
    # f.write(this_data.prettify())
    # f.close()
