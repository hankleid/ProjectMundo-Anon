from translation import Translator, GPT
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
        if code == 'eng':
            article = get_nature_article(doi)
            add_mathML(article)
            save_text(article_fd+f"/{code}.xml", article.prettify())
        else:
            print("Article hasn't been translated yet!")
            return
    if code == 'eng':
        txt_fn = 'eng_full.txt'
    else:
        txt_fn = f'{code}.txt'
    if not os.path.isfile(fulltxt_fd+f"/{txt_fn}"):
        # extract plain text from XML
        xml = None
        with open(article_fd+f"/{code}.xml", 'r') as f:
            xml = "".join(f.readlines())
            xml = BeautifulSoup(xml, features="xml")
        save_fulltext(get_copy(xml), fulltxt_fd+f"/{txt_fn}")

def filter_qs(questions: dict, quiz_dir: str, answer_dir: str, label: str):
    # questions: QA
    # answer dir: path to folder with answerkey
    # label: (fn-ish) for saving the nocontext json

    # questions = load_json(path+"/"+qna_name)
    prompt = f"Please read the entire prompt before responding. Here are questions about the contents of some scientific article:\n{questions}\n\nBased on your training data alone, please answer all of these multiple choice questions to the best of your ability. Do not make guesses. If you are not sure, select 'F' ('I don't know') as your answer. Report your answers as a JSON where the keys are the question numbers and the values are your letter answers."

    fn = f"{label}_nocontext_answers.json"

    temp = tl.temp
    tl.temp = 0
    res = tl.prompt_get_json(prompt)
    tl.temp = temp
    save_text(quiz_dir+"/"+fn, res)

    answers = load_json(quiz_dir+"/"+fn)
    incorrect = grade(quiz_dir+"/"+fn,answer_dir)

    num_qs = len(list(answers.keys()))
    num_incorrect = len(list(incorrect.keys()))
    
    return num_qs, num_incorrect

def generate_qs(num_qs, save_path, eng_path):
    # save_path folder to save QnA jsons
    # eng_path path to english full text file

    q_prompt = f"Please read the following scientific text, which represents a scientific article. Generate {num_qs} detailed and specific questions to test a reader's understanding of the findings of the article. Each question should be unique. The questions should labeled 1-{num_qs}. The questions should be multiple choice with 6 possible answers: 5 are labeled A-E, and the 6th option should say 'I don't know'. There should only be one correct answer from the options. The questions should cover the unique results, figures, and tables of the article as much as possible. If you are able to answer any of the questions without having read the article, please generate a better question. Please format your response as a JSON object with the question, possible answers, and correct answers. The JSON key to each question should be its number. Here is the scientific text: "
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

    return questions, answerkey

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

def grade(quiz_path: str, answer_dir: str):
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

# ROUTINES

def evaluate_contamination(doi: str, num_qs: int, qna_save_folder: str):
    # gets the article at the DOI -> extracts the full text
    # generates the QA -> executes the QA -> returns result
    make_fulltext(doi, 'English')
    save_path = f"FullTexts/{filename_from_DOI(doi=doi)}/"
    qna_path = save_path+f'/{qna_save_folder}'
    if not os.path.isdir(qna_path):
        os.mkdir(qna_path)

    # questions = load_json(save_path+f'/{num_qs}q_temp{tl.temp}_gpt_nocontext_answers.json')
    questions, _ = generate_qs(num_qs, qna_path, eng_path=save_path+'/eng_full.txt')
    _, num_incorrect = filter_qs(questions, quiz_dir=qna_path, answer_dir=qna_path, label='QnA')

    print(f"Without context, the model answered {num_qs-num_incorrect} of {num_qs} correct.")
    

if __name__ == "__main__":
    # make_fulltexts()

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

    # article first draft
    article10 = "10.1038/s41598-023-51013-3" # sci rep 2 **
    article11 = "10.1038/s41598-023-43026-9" # biochem, endochrinology, neuroscience **
    article12 = "10.1038/s41598-023-45072-9" # covid **
    article13 = "10.1038/s41467-023-43949-x" # quantum optics **
    article14 = "10.1038/s41467-023-43067-8" # drug delivery **
    article15 = "10.1038/s41467-023-43963-z" # materials science **

    # article second draft
    # (* for context-checked)
    # (** for * and QA for GPT translations)
    articles2 = [
        # Health Sciences
        "10.1038/s41467-023-44276-x", #** Risk of COVID-19 death in adults who received booster COVID-19 vaccinations in England
        "10.1038/s41467-024-52894-2", #** Plasma proteomic and polygenic profiling improve risk stratification and personalized screening for colorectal cancer
        "10.1038/s41467-024-48700-8", #* Cosmic kidney disease: an integrated pan-omic, physiological and morphological study into spaceflight-induced renal dysfunction
        "10.1038/s41467-024-46116-y", #** Effect of gut microbiome modulation on muscle function and cognition: the PROMOTe randomised controlled trial
        # "10.1038/s41467-024-49634-x", #* Cohort study of cardiovascular safety of different COVID-19 vaccination doses among 46 million adults in England
        # Life and Biological Sciences
        "10.1038/s41467-024-45446-1", #** Children born after assisted reproduction more commonly carry a mitochondrial genotype associating with low birthweight
        "10.1038/s41467-024-47940-y", #** Gene editing for latent herpes simplex virus infection reduces viral load and shedding in vivo
        "10.1038/s41467-024-53453-5", #** 3D chromatin maps of a brown alga reveal U/V sex chromosome spatial organization
        "10.1038/s41467-024-52388-1", #** CRISPR/Cas9 editing of NKG2A improves the efficacy of primary CD33-directed chimeric antigen receptor natural killer cells
        # "10.1038/s41467-024-46089-y", #* Drug target prediction through deep learning functional representation of gene signatures
        # Social Science and Human Behavior
        "10.1038/s41467-024-46581-5", #* Worldwide divergence of values
        "10.1038/s41467-024-46161-7", #* The Persian plateau served as hub for Homo sapiens after the main out of Africa dispersal
        "10.1038/s41467-024-48512-w", #* Systematic review and meta-analysis of ex-post evaluations on the effectiveness of carbon pricing
        "10.1038/s41467-024-44770-w", #* People quasi-randomly assigned to farm rice are more collectivistic than people assigned to farm wheat
        # "10.1038/s41467-024-44693-6", #* Psychological well-being in Europe after the outbreak of war in Ukraine
        # Chemistry and Materials Science
        "10.1038/s41467-024-46016-1", #* The first demonstration of entirely roll-to-roll fabricated perovskite solar cell modules under ambient room conditions
        "10.1038/s41467-024-45461-2", #* DynamicBind: predicting ligand-specific protein-ligand complex structure with a deep equivariant generative model
        "10.1038/s41467-024-49753-5", #* Lithium-ion battery components are at the nexus of sustainable energy and environmental release of per- and polyfluoroalkyl substances
        "10.1038/s41467-024-48779-z", #* Physics-informed neural network for lithium-ion battery degradation stable modeling and prognosis
        # "10.1038/s41467-023-44481-8", #* Bioinspired structural hydrogels with highly ordered hierarchical orientations by flow-induced alignment of nanofibrils
        # Earth, Environmental and Planetary Sciences
        "10.1038/s41467-024-51355-0", #* Significantly wetter or drier future conditions for one to two thirds of the world’s population
        "10.1038/s41467-024-51879-5", #* Florida Current transport observations reveal four decades of steady state
        "10.1038/s41467-024-45487-6", #* Real-world time-travel experiment shows ecosystem collapse due to anthropogenic climate change
        "10.1038/s41467-023-43832-9", # The first ice-free day in the Arctic Ocean could occur before 2030
        # "10.1038/s41467-024-52631-9", #* Animal life in the shallow subseafloor crust at deep-sea hydrothermal vents
        # Physics
        "10.1038/s41467-024-49689-w", #* Amplification of electromagnetic fields by a rotating body
        "10.1038/s41467-024-48575-9", #* Zero-shot learning enables instant denoising and super-resolution in optical fluorescence microscopy
        "10.1038/s41467-024-45586-4", #* Current-induced switching of a van der Waals ferromagnet at room temperature
        "10.1038/s41467-024-46372-y", #* Ultra-fast switching memristors based on two-dimensional materials
        # "10.1038/s41467-024-45888-7", #* General-purpose programmable photonic processor for advanced radiofrequency applications
    ]
    
    articles3 = ["10.1038/s41467-024-48700-8","10.1038/s41467-024-51355-0","10.1038/s41467-023-43832-9"]
    
    languages2 = [
        "English",
        "Chinese (simplified characters)",
        "German",
        "French",
        "Hindi",
        "Spanish",
        "Hebrew",
        "Turkish",
        "Russian",
        "Farsi",
        "Swahili",
    ]

    articles = [filename_from_DOI(doi=doi) for doi in [article10,article11,article12,article13,article14,article15]]

    langs_dict = load_langs()['translation']
    # langs = [l for l in langs_dict.keys() if l != 'Slovene']
    langs = languages2
    # langs = langs[langs.index("Farsi"):]
    # langs = ["English"]

    model = GPT()
    tl = Translator(model)
    contam_check = False
    # 2, 16, 19
    for doi in articles3:
        a = filename_from_DOI(doi=doi)
        print(a)
        if contam_check:
            print("Checking for contamination.")
            model.temp = 1
            evaluate_contamination(doi, 50, "50q_temp1_gpt")
            contam_check = False

        qna_path = f"FullTexts/{a}/50q_temp1_gpt"
        if not os.path.isdir(qna_path):
            os.mkdir(qna_path)
        save_path = qna_path + "/gpt_translated"
        if not os.path.isdir(save_path):
            os.mkdir(save_path)

        for lang in langs:
            make_fulltext(doi, lang)
            print(lang)
            code = langs_dict[lang]

            if code == "eng":
                qna_fn = "QnA.json"
                text_fn = "eng_full.txt"
            else:
                qna_fn = f"QnA_{code}.json"
                text_fn = f"{code}.txt"
            answers_fn = f"QnA_{code}_answers.json"

            # model.temp = 0
            # if code != "eng":
            #     translate_qs(lang, qna_path, qna_fn)

            model.temp = 0
            quiz(lang, save_path=save_path+"/"+answers_fn,
                 article_path=f"FullTexts/{a}/{text_fn}",
                 qna_path=qna_path+"/"+qna_fn)
            print(lang, grade(quiz_path=save_path+"/"+answers_fn,
                              answer_dir=qna_path))
        print(a)
