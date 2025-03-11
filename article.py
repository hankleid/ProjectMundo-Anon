import requests
from bs4 import BeautifulSoup
import time
import json
from typing import Union as u

# ARTICLE ACQUISITION

def get_nature_article(doi):
    # Returns the Nature article @ doi in JATS (XML) format
    key = ""
    with open("../keys/nature_key.txt") as f:
        key = f.readline()

    URL = "http://api.springernature.com/openaccess/jats?"
    PARAMS = {
        "q": f"doi:{doi}",
        "api_key": key
    }
    r = requests.get(url=URL, params=PARAMS)


    data = BeautifulSoup(r.content, features="xml")
    # Enter correct XSLT style information.
    data.contents[0].replace_with(BeautifulSoup('<?xml-stylesheet type="text/xsl" href="/style/jats-html.xsl"?>', features="xml"))
    # Remove the API response portion of the XML.
    data.response.replace_with(data.records.article)

    return data

def get_aps_article(doi):
    # Returns the APS article @ doi in JATS (XML) format
    URL = f"http://harvest.aps.org/v2/journals/articles/{doi}"
    HEADERS = {
        "Accept": "text/xml"
    }
    r = requests.get(url=URL, headers=HEADERS)

    data = BeautifulSoup(r.content, features="xml")
    data.insert(0, BeautifulSoup('<?xml-stylesheet type="text/xsl" href="/style/jats-html.xsl"?>', features='xml'))
    return data

def get_copy(xml):
    # Returns a copied BeautifulSoup object
    copy = BeautifulSoup(str(xml), features="xml")
    if copy.find(xml.name):
        return copy.find(xml.name)
    else:
        return copy

def load_text(path):
    with open(path, "r") as f:
      try:
        lines = f.readlines()
        return ''.join(lines)
      except:
        print("Article not found!")

def save_text(path, s):
    with open(path, "w+") as f:
        f.write(s)

def load_json(path):
    d = {}
    with open(path, "r") as f:
        d = json.load(f)
    return d

def save_json(path, d):
    with open(path, "w+") as f:
        json.dump(d, f, indent=4)

def save_fulltext(xml, fn):
    # Saves the raw text (exluding equations) to a file
    # to be used as context for the translator.
    this = get_copy(xml)
    fulltext = ""

    # REMOVE CITATIONS TO OTHER ARTICLES AND TEX-MATH
    for x in [_ for _ in this.body.find_all("xref") if _['ref-type'] and _['ref-type'] == "bibr"]+[_ for _ in this.body.find_all("tex-math")]:
        x.clear(decompose=True)

    # ADD BRACKETS TO TABLE/FIG REFERENCES FOR READABILITY
    for ref in [_ for _ in this.body.find_all('xref') if _.has_attr('ref-type') and _['ref-type'] != 'bibr']:
        ref.string = f" [{ref.string.strip()}] "

    # REMOVE TABLES AND FIGURES BUT SAVE FOR PRINTING AT END
    figs, tabs = [], []
    for f in this.body.find_all("fig"):
        figs.append(get_copy(f))
        f.clear(decompose=True)
    for t in this.body.find_all("table-wrap"):
        tabs.append(get_copy(t))
        t.clear(decompose=True)

    # ADD TITLE AND ABSTRACT TO DOCUMENT
    fulltext += stripped(this.front.find("article-title").find_all(text=True)) + "\n\n"
    if this.front.find("abstract").find("title"):
        fulltext += stripped(this.front.find("abstract").find("title").find_all(text=True)) + ": "
        this.front.find("abstract").find("title").clear(decompose=True)
    fulltext += stripped(this.front.find("abstract").find_all(text=True)) + "\n\n"

    # ADD THE BODY OF THE ARTICLE
    for p in [_ for _ in this.body.find_all('p')]:# if _.has_attr('id')]:
        fulltext += stripped(p.find_all(text=True)) + "\n\n"

    # ADD TABLES
    for t in tabs:
        fulltext += stripped(t.find("label").find_all(text=True)) + ": " + stripped(t.find("caption").find_all(text=True)) + "\n"
        header = [_ for _ in t.find("thead").find_all("th")]
        if header:
            fulltext += stripped(["".join(h.find_all(text=True)) + "| " for h in header[:-1]] + header[-1].find_all(text=True)) + "\n"
        body_rows = [_ for _ in t.find("tbody").find_all("tr")]
        for r in body_rows:
            cols = r.find_all("td")
            fulltext += stripped(["".join(c.find_all(text=True)) + "| " for c in cols[:-1]] + cols[-1].find_all(text=True)) + "\n"
        if t.find("table-wrap-foot"):
            fulltext += stripped(t.find("table-wrap-foot").find_all(text=True)) + "\n\n"
        else:
            fulltext += "\n"

    # ADD FIGURES
    for f in figs:
        fulltext += stripped(f.find("label").find_all(text=True)) + ": "
        cap = f.find("caption").find("p")
        if cap:
            captext = ""
            for child in cap.children:
                if child.name == None:
                    captext += child.string
                elif child.name == "bold":
                    captext += child.string.strip() + "  "
                else:
                    captext += "".join(child.find_all(text=True)) + " "
        fulltext += stripped(captext) + "\n\n"
    
    fulltext.replace(" .", ".").replace(" ,", ",")
    # SAVE FULLTEXT
    with open(fn, "w+") as f:
        f.write(fulltext)


def stripped(string, maxspaces=11):
    string_stripped = "".join(string).replace("\n", "")
    spaces = ""
    count = 0
    while count <= maxspaces-3:
        for _ in range(maxspaces-count):
            spaces += " "
        if len(spaces) % 2:
            string_stripped = string_stripped.replace(spaces, "")
        else:
            string_stripped = string_stripped.replace(spaces, " ")
        spaces = ""
        count += 1
    return string_stripped.replace(" .", ".").strip()

# TRANSLATION EXECUTION FUNCTIONS

def parse_sups(this_sups):
    # returns a list of reference elements from a list of sup elements.
    refs = []
    for sup in this_sups:
        i = 0
        for ref in sup.find_all('xref'):
            if i != 0:
                refs.append(",")
            refs.append(ref)
            i += 1

    sup = BeautifulSoup("<sup></sup>",features='xml')
    for ref in refs:
        sup.sup.append(ref)
    return sup.sup

def parse_par(this_par):
    # rearranges this paragraph such that the references appear at the end of its respective sentence, not inside the sentence.
    # returns the number of figures in this paragraph.
    # returns the number of tables in this paragraph.
    numfigs, numtables = 0, 0
    sentences = []
    sups = []
    curr_sent = ""
    new_par = BeautifulSoup("<p></p>",features='xml')

    children = [s for s in this_par.children]
    for s in children:
        if s.name == 'sup':
            sups.append(s)
        elif s.name == 'fig':
            numfigs += 1
            s.decompose()
        elif s.name == 'table-wrap':
            numtables += 1
            s.decompose()
        elif s.name != None:
            sentences.append(curr_sent)
            curr_sent = ""
            sentences.append(s)
        elif s.string != None:
            if s.string[0] != '.':
                curr_sent += s.string
            else:
                # end of sentence. append the current one and start a new one.
                sentences.append(curr_sent)
                curr_sent = s.string

                # include the references for the previous sentence.
                sentences.append(parse_sups(sups))
                sups = []

    sentences.append(curr_sent)
    if sups != []:
        sentences[-1] = sentences[-1][0:-1] # remove period
        sentences.append(parse_sups(sups))
        sentences.append(".")

    new_par.p.extend(sentences)

    this_par.clear()
    this_par.extend(new_par.p.contents)
    return numfigs, numtables

def split_to_parts(xml, numparts):
    # xml list of xml objects
    # numparts number of lists to split into

    if numparts == 0:
        return []
    elif numparts == 1:
        return [xml]
    else:
        l, split = len(xml), []
        for i in range(numparts):
            split.append(xml[i*l//numparts:(i+1)*l//numparts])
        return split
    
def append_to_pars(xml, locs, toadd):
    # xml body to search for paragraphs
    # locs dictionary linking paragraph ids to num of extras
    # extras the extras to add
    if isinstance(locs, int):
        # paragraphs have no ids; add to end of paper before conclusion.
        par = xml.find_all('sec')[locs]
        for t in toadd:
            par.append(t)
    else:
        i = 0
        for p, num_toadd in zip(locs.keys(), locs.values()):
            par = xml.find('p', {'id': p})
            for _ in range(num_toadd):
                par.append(toadd[i])
                i += 1

def translate_single(xml, tl, language, inplace=True):
    try:
        print(xml['id'])
    except:
        print(f"(no id) {xml.name}")

    result = tl.translate_xml(xml, language)
    new_xml = BeautifulSoup(result, features="xml")
    if inplace:
        guts = new_xml.find(xml.name).contents
        xml.clear()
        xml.extend(guts)
    else:
        return new_xml.find(xml.name)
    
def translate_list(xml, tl, language, inplace=True):
    ids = []
    for x in xml:
        try:
            ids.append(x['id'])
        except:
            ids.append(f"(no id) {x.name}")
    print(ids)

    result = tl.translate_xml(xml, language)
    new_xml = [BeautifulSoup(res, features="xml") for res in result]
    if inplace:
        for i in range(len(new_xml)):
            guts = new_xml[i].find(xml[i].name).contents
            xml[i].clear()
            xml[i].extend(guts)
    else:
        return [new_x.find(old_x.name) for new_x, old_x in zip(new_xml, xml)]

def translate(xml: u[str,list], tl, language, inplace=True, delay=False):
    # translates the chunk in place.
        # xml: article to translate
        # tl: Translator object
        # language: language to translate to
        # text (bool): true if only want to translate string, not whole xml obj.
        # delay (bool): true if want to pause before translating. good for avoiding query frequency limits.
    if delay:
        time.sleep(0.5)
    
    # Printing for guiding the eye.
    is_list = isinstance(xml, list)
    if not is_list and xml:
        return translate_single(xml, tl, language, inplace=inplace)
    else:
        xml = [x for x in xml if x]
        return translate_list(xml, tl, language, inplace=inplace)

def chunkify(xml):
    # returns the objects to translate in [[],[]] form
    # parses pars and returns the figure and table locations
    front = xml.front
    body = xml.body
    back = xml.back

    # Restructure the sentences. Save the figures since we take them out here.
    par_num_lim, fig_num_lim, tab_num_lim, titles_num_lim = 1, 2, 2, 20

    figures = [get_copy(fig) for fig in body.find_all('fig')]
    tables = [get_copy(tab) for tab in body.find_all('table-wrap')]

    tables = split_to_parts(tables, len(tables)//tab_num_lim)
    figures = split_to_parts(figures, len(figures)//fig_num_lim)

    fig_locations, tab_locations = {}, {}
    for p in body.find_all('p'):
        numfigs, numtabs = parse_par(p)
        if numfigs > 0:
            try:
                fig_locations[p['id']] = numfigs
            except: # old papers don't have paragraph ids.
                pass
        if numtabs > 0:
            try:
                tab_locations[p['id']] = numtabs
            except: # old papers don't have paragraph ids.
                pass
    if fig_locations == {} and tab_locations == {}:
        # old papers don't have paragraph ids; set locations to the par before discussion.
        secs = body.find_all('sec')
        for i in range(len(secs)):
            if (secs[i].find('title').string == "Summary"
               or secs[i].find('title').string == "Discussion"
               or secs[i].find('title').string == "Conclusion"
               or secs[i].find('title').string == "Conclusions"):
                fig_locations, tab_locations = i-1, i-1
                break

    pars = [p for p in body.find_all('p') if p.has_attr('id')]
    split_pars = split_to_parts(pars, len(pars)//par_num_lim)

    # titles = [title for title in xml.find_all('title')]
    # titles = split_to_parts(titles, len(titles)//titles_num_lim)

    # Translate the article title and abstract.
    # Translate the body. Translate figures independently so the translator doesn't get confused.
    # Translate acknowledgements and author contributions.
    # Translate the (sub)titles in case they were missed. 
    to_translate = [[front.find('article-title'),
                     front.find('abstract'),
                     back.find('ack'), back.find('sec', {'sec-type': 'author-contribution'})],
                     [title for title in xml.find_all('title')]]
    

    for chunk in tables+figures+split_pars:
        to_translate.append(chunk)
        
    to_translate = [x for x in to_translate if x]

    return to_translate, fig_locations, tab_locations


def translate_article(xml, tl, language):
    # edits xml in place with translated text.
        # xml: article to translate
        # tl: Translator object
        # language: language to translate to

    to_translate, fig_locations, tab_locations = chunkify(xml)
    
    newfigs, newtabs = [], []
    if tl.use_context:
        for x in to_translate:
            if x[0].name == 'fig':
                newfigs += translate(x,tl,language,inplace=False,delay=True)
            elif x[0].name == 'table-wrap':
                newtabs += translate(x,tl,language,inplace=False,delay=True)
            else:
                translate(x,tl,language,delay=True)
    else:
        for _ in to_translate:
            for x in _:
                if x.name == 'fig':
                    newfigs.append(translate(x,tl,language,inplace=False))
                elif x.name == 'table-wrap':
                    newtabs.append(translate(x,tl,language,inplace=False))
                else:
                    translate(x,tl,language)

    # Replace the translated figures.
    if len(newfigs) > 0:
        append_to_pars(xml.body, fig_locations, newfigs)
    if len(newtabs) > 0:
        append_to_pars(xml.body, tab_locations, newtabs)


#################################
######### I/O FUNCTIONS #########
##### XML EDITING FUNCTIONS ##### 
#################################
            
def load_langs():
    return json.load(open('lang.json'))

def load_articles():
    return json.load(open('articles.json'))

def add_mathML(xml):
    # Adds the MathML attribute for displaying equations.
    for math in xml.find_all('math'):
        math['xmlns'] = "http://www.w3.org/1998/Math/MathML"

def filename_from_DOI(xml=None, doi=None, language=None):
    filename = ""
    if xml and not doi:
        # collect doi from article
        doi = xml.front.find('article-meta').find('article-id', {'pub-id-type': 'doi'}).string
    
    filename = doi.replace('/','_').replace('.','X')
    
    if language:
        codes = load_langs()
        filename += f"_{codes[language]}"

    return str_strip(filename)

def change_graphic_dir(xml):
    dir = f"/ProjectMundo-Anon-106A/MediaObjects/{filename_from_DOI(xml=xml)}"

    def _change_graphic_dir(linkstr):
        graphics = [graphic for graphic in xml.find_all('graphic') if graphic.has_attr(linkstr) and 'MediaObjects' in graphic[linkstr]]
        for graphic in graphics:
            curr_dir = graphic[linkstr]
            fn = curr_dir[curr_dir.rindex('/'):]
            graphic[linkstr] = (dir+fn).replace("\n","").replace(" ","")
    
    _change_graphic_dir('href')
    _change_graphic_dir('xlink:href')

def str_strip(string):
    return string.replace("\n","").strip()



