from translation import Translator
from article import *
import os

def make_fulltext(doi, lang):
    code = load_langs()['translation'][lang]
    doi_fn = filename_from_DOI(doi=doi)
    fulltxt_fd = f"FullTexts/{doi_fn}"
    article_fd = f"articles/{doi_fn}"
    if not os.path.isdir(fulltxt_fd):
        os.mkdir(fulltxt_fd)
    if not os.path.isdir(article_fd):
        os.mkdir(article_fd)   
    if not os.path.isfile(article_fd+f"/{code}.xml"):
        article = get_nature_article(doi)
        add_mathML(article)
        save_text(article_fd+f"/{code}.xml", article.prettify())
    if not os.path.isfile(fulltxt_fd+f"/{code}_full.txt"):
        xml = None
        with open(article_fd+f"/{code}.xml", 'r') as f:
            xml = "".join(f.readlines())
            xml = BeautifulSoup(xml, features="xml")
        save_fulltext(get_copy(xml), fulltxt_fd+f"/{code}_full.txt")

def filter_qs(path, qna_name):
    # path where QnA, answer key, and no context answers will be.
    # qna_name name of the questions file to test without context.

    questions = load_json(path+"/"+qna_name)
    prompt1 = f"Please read the entire prompt before responding. Here are questions about the contents of some scientific article:\n{questions}\n\nBased on your training data alone, please answer all of these multiple choice questions to the best of your ability. Do not make guesses. If you are not sure, select 'F' ('I don't know') as your answer. Report your answers as a JSON where the keys are the question numbers and the values are your letter answers."

    fn = f"{qna_name[:-5]}_nocontext_answers.json"

    temp = tl.temp
    tl.temp = 0
    res = tl.prompt_get_json(prompt1)
    tl.temp = temp
    save_text(path+"/"+fn, res)

    answers = load_json(path+"/"+fn)
    incorrect = grade(path, fn)

    num_qs = len(list(answers.keys()))
    num_incorrect = len(list(incorrect.keys()))
    print(f"Without context, the model answered {num_qs-num_incorrect} of {num_qs} correct.")


def generate_qs(num_qs, save_path, eng_path):
    # save_path folder to save QnA jsons
    # eng_path path to english full text file

    q_prompt = f"Please read the following scientific journal article. Generate {num_qs} detailed and specific questions to test a reader's understanding of the findings of the article. Each question should be unique. The questions should labeled 1-{num_qs}. The questions should be multiple choice with 6 possible answers: 5 are labeled A-E, and the 6th option should say 'I don't know'. There should only be one correct answer from the options. The questions should cover the unique results, figures, and tables of the article as much as possible. If you are able to answer any of the questions without having read the article, please generate a better question. Please format your response as a JSON object with the question, possible answers, and correct answers. The JSON key to each question should be its number. Here is the article: "
    q_prompt += "\n"+load_text(eng_path)
    # q_prompt = f"Please read the following scientific journal article. Generate {num_qs} detailed and specific questions to test a reader's understanding, targeting the tables and figures only. Each question should be unique. The questions should labeled 1-{num_qs}. The questions should be multiple choice with 5 possible answers labeled A-E. There should only be one correct answer from the options. The questions should be as specific to the tables and figures as possible. Please format your response as a JSON object with the question, possible answers, and correct answers. The JSON key to each question should be its number. Here is the article and the figures: "

    res = tl.prompt_get_json(q_prompt, figs=False)
    save_text(save_path+"/QnA.json", res)
    qna = load_json(save_path+"/QnA.json")

    # check for duplicate questions
    qs_i, qs = [], []
    repeats = []
    for i in qna.keys():
        q =  qna[i]['question']
        if q in qs:
            repeats.append({i: q})
        qs_i.append(i)
        qs.append(q)
    print(repeats, len(repeats))

    # remove answer key and save it in separate file
    answerkey, questions = {}, {}
    for i in range(num_qs):
        key = str(i+1)
        q, choices, a = tuple(qna[key].keys())
        answerkey[key] = qna[key][a]
        questions[key] = {
            "question": qna[key][q],
            "options": qna[key][choices]
        }

    save_json(save_path+"/QnA_answerkey.json", answerkey)
    save_json(save_path+"/QnA.json", questions)

def translate_qs(lang, path, savename):
    # path where questions are and where to save the translated questions.

    prompt = f"The following JSON comprises a list of questions about an academic journal article. Please translate the questions and options into {lang}. Do not translate the keys of the JSON. Please return the translated JSON. Here is the JSON to translate: \n{load_json(path+'/QnA.json')}"

    res = tl.prompt_get_json(prompt, path+"/QnA.json")
    save_text(path+"/"+savename, res)
    
def quiz(lang, save_path, article_path, qna_path):
    prompt = f"Please read the following scientific journal article"
    if lang != "English":
        prompt += f", which has been translated into {lang}."
    prompt += f"Then answer the questions based on your understanding. Report your answers as a JSON where the keys are the question numbers and the values are your letter answers. Here is the article to read: '{load_text(article_path)}'\n\n and here are the questions:\n\n{load_json(qna_path)}.\n\nIf you do not know the answer, select 'I don't know' as your answer. Do not make guesses."

    res = tl.prompt_get_json(prompt, figs=False)

    save_text(save_path, res)

def grade(quiz_path, answer_dir):
    # path to answer key and quiz to grade
    # quizname name of the json file with quiz response

    answerkey = load_json(answer_dir+"/QnA_answerkey.json")
    test = load_json(quiz_path)
    
    incorrect = {}
    for i in answerkey.keys():
        answer = ""
        if isinstance(test[i], list):
            answer = test[i][0]
            correct = answerkey[i] == answer
        else:
            answer = test[i]
            correct = answerkey[i] == answer
        test[i] = [answer, correct]
        if not correct:
            incorrect[i] = answer

    save_json(quiz_path, test)
    return incorrect


if __name__ == "__main__":
    # make_fulltexts()

    doi1 = "10.1038/s41586-024-07386-0" # Choi (kor)

    article1 = "10.1038/s41467-023-43444-3" # health
    article2 = "10.1038/s41467-018-04608-8" # zou
    article3 = "10.1038/s41467-023-42766-6" # cats
    article4 = "10.1038/s41467-017-00516-5" # Ahn et al.
    article5 = "10.1038/s41467-019-11343-1" # Jelena
    article6 = "10.1038/s41467-023-40666-3" # human behavior

    article7 = "10.1038/s41598-023-44786-0" # le
    article8 = "10.1038/s41586-024-07386-0" # choi
    article9 = "10.1038/s41467-023-44527-x" # kim

    doi1 = "10.1038/s42005-020-00412-3" # Mayor (fra)
    doi1 = "10.1038/s41746-019-0216-8" # Ghorbani (per)
    doi1 = "10.1038/s41377-020-00354-z" # Lustig (heb)

    article10 = "10.1038/s41598-023-51013-3" # sci rep 2 **
    article11 = "10.1038/s41598-023-43026-9" # biochem, endochrinology, neuroscience **
    article12 = "10.1038/s41598-023-45072-9" # covid **
    article13 = "10.1038/s41467-023-43949-x" # quantum optics **
    article14 = "10.1038/s41467-023-43067-8" # drug delivery **
    article15 = "10.1038/s41467-023-43963-z" # materials science **


    articles = [filename_from_DOI(doi=doi) for doi in [article10,article11,article12,article13,article14,article15]]

    langs_dict = load_langs()['translation']
    langs = [l for l in langs_dict.keys()]
    # langs = langs[langs.index("Bengali"):]
    langs = ["Hebrew"]

    tl = Translator("gpt")
    for doi in [doi1]:#articles[4:5]:
        a = filename_from_DOI(doi=doi)
        make_fulltext(doi, "Hebrew")
        print(a)
        qna_path = f"FullTexts/{a}/50q_temp1_f_gpt"
        if not os.path.isdir(qna_path):
            os.mkdir(qna_path)
        save_path = qna_path + "/google_translated_engq"
        if not os.path.isdir(save_path):
            os.mkdir(save_path)
        # eng_path = f"FullTexts/{a}/eng_full.txt"

        # tl.temp = 1
        # generate_qs(50, save_path, eng_path)
        # filter_qs(save_path, "QnA.json")

        for lang in langs:
            # make_fulltext(doi, lang)
            print(lang)
            code = langs_dict[lang]

            if code == "eng":
                qna_fn = "QnA.json"
                text_fn = "eng_full.txt"
            else:
                qna_fn = "QnA.json" # f"QnA_{code}.json"
                text_fn = f"{code}_google.txt"
            answers_fn = f"QnA_{code}_answers.json"

            # tl.temp = 0
            # if code != "eng":
            #     translate_qs(lang, save_path, qna_fn)

            tl.temp = 1
            quiz(lang, save_path=save_path+"/"+answers_fn,
                 article_path=f"FullTexts/{a}/{text_fn}",
                 qna_path=qna_path+"/"+qna_fn)
            print(lang, grade(quiz_path=save_path+"/"+answers_fn,
                              answer_dir=qna_path))
