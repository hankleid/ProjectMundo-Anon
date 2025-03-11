import requests
import tools

def gen_dois(year):
    # Records the DOIs of all Nature articles in the year given.
    # Returns a list of all the DOIs sorted by date.

    key = ""
    with open("../keys/nature_key.txt") as f:
        key = f.readline()

    URL = "http://api.springernature.com/meta/v2/json?"
    perpage = 25 # maximum value from basic API

    PARAMS = {
        "q": f'(datefrom:"{year}-01-01" AND dateto:"{year}-12-01" AND journalid:"41586")',
        "s": 1,
        "p": perpage,
        "api_key": key
    }

    dois = [] # list of {year: doi} pairs

    i = 0
    while True:
        print(i)
        PARAMS['s'] = i * perpage + 1
        r = requests.get(url=URL, params=PARAMS).json()

        articles = [a for a in r['records'] if (a['openaccess'] == 'true' and 'OriginalPaper' in a['genre'])]
        for a in articles:
            dois.append({tools.date_score(a['publicationDate']): a['doi']})
        
        if len(r['records']) < perpage: break # final page
        i += 1

    dois = sorted(dois, key=lambda d: list(d.keys())[0])
    [print(d,"\n") for d in dois]

    return dois

def save_dois(dois, path):
    with open(path, "w+") as f:
        st = ""
        for d in dois:
            st += f"{list(d.values())[0]} {list(d.keys())[0]}\n"
        f.write(st)

if __name__ == "__main__":
    dois = gen_dois(2024)
    print(len(dois))
    save_dois(dois, 'DoiLists/2024.txt')