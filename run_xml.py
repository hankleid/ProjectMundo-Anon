from translation import Translator, GPT, Llama, Qwen
from article import *
import tools
import os
import time

# doi = "10.1038/s41467-023-43444-3" # health
# doi = "10.1038/s41467-024-52834-0" # Hsu et al.
# doi = "10.1038/s41467-018-04608-8" # zou
doi = "10.1038/s41467-023-42766-6" # cats
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
# doi = "10.1038/s41467-024-50750-x" # Franco-Rubio (spa)

# doi = "10.1038/s41598-023-51013-3" # sci rep 2
# doi = "10.1038/s41598-023-43026-9" # sci rep 3
# doi = "10.1038/s41598-023-45072-9" # covid
# doi = "10.1038/s41467-023-43949-x" # quantum optics
# doi = "10.1038/s41467-023-43067-8" # drug delivery *
# doi = "10.1038/s41467-023-43963-z" # materials science *

# article second draft
# (* for GPT translated)
articles2 = [
    # Health Sciences
    "10.1038/s41467-023-44276-x", #* Risk of COVID-19 death in adults who received booster COVID-19 vaccinations in England
    "10.1038/s41467-024-52894-2", #* Plasma proteomic and polygenic profiling improve risk stratification and personalized screening for colorectal cancer
    "10.1038/s41467-024-45260-9", #* Fasting-mimicking diet causes hepatic and blood markers changes indicating reduced biological age and disease risk
    "10.1038/s41467-024-46116-y", #* Effect of gut microbiome modulation on muscle function and cognition: the PROMOTe randomised controlled trial
    # "10.1038/s41467-024-49634-x", # Cohort study of cardiovascular safety of different COVID-19 vaccination doses among 46 million adults in England
    # Life and Biological Sciences
    "10.1038/s41467-024-45446-1", #* Children born after assisted reproduction more commonly carry a mitochondrial genotype associating with low birthweight
    "10.1038/s41467-024-47940-y", #* Gene editing for latent herpes simplex virus infection reduces viral load and shedding in vivo
    "10.1038/s41467-024-53453-5", #* 3D chromatin maps of a brown alga reveal U/V sex chromosome spatial organization
    "10.1038/s41467-024-52388-1", #* CRISPR/Cas9 editing of NKG2A improves the efficacy of primary CD33-directed chimeric antigen receptor natural killer cells
    # "10.1038/s41467-024-46089-y", # Drug target prediction through deep learning functional representation of gene signatures
    # Social Science and Human Behavior
    "10.1038/s41467-024-46581-5", #* Worldwide divergence of values
    "10.1038/s41467-024-46161-7", #* The Persian plateau served as hub for Homo sapiens after the main out of Africa dispersal
    "10.1038/s41467-024-48512-w", #* Systematic review and meta-analysis of ex-post evaluations on the effectiveness of carbon pricing
    "10.1038/s41467-024-44770-w", #* People quasi-randomly assigned to farm rice are more collectivistic than people assigned to farm wheat
    # "10.1038/s41467-024-44693-6", # Psychological well-being in Europe after the outbreak of war in Ukraine
    # Chemistry and Materials Science
    "10.1038/s41467-024-46016-1", #* The first demonstration of entirely roll-to-roll fabricated perovskite solar cell modules under ambient room conditions
    "10.1038/s41467-024-45461-2", #* DynamicBind: predicting ligand-specific protein-ligand complex structure with a deep equivariant generative model
    "10.1038/s41467-024-49753-5", #* Lithium-ion battery components are at the nexus of sustainable energy and environmental release of per- and polyfluoroalkyl substances
    "10.1038/s41467-024-48779-z", #* Physics-informed neural network for lithium-ion battery degradation stable modeling and prognosis
    # "10.1038/s41467-023-44481-8", # Bioinspired structural hydrogels with highly ordered hierarchical orientations by flow-induced alignment of nanofibrils
    # Earth, Environmental and Planetary Sciences
    "10.1038/s41467-024-47676-9", #* Continuous sterane and phytane δ13C record reveals a substantial pCO2 decline since the mid-Miocene
    "10.1038/s41467-024-51879-5", #* Florida Current transport observations reveal four decades of steady state
    "10.1038/s41467-024-45487-6", #* Real-world time-travel experiment shows ecosystem collapse due to anthropogenic climate change
    "10.1038/s41467-024-54508-3", #* The first ice-free day in the Arctic Ocean could occur before 2030
    # "10.1038/s41467-024-52631-9", # Animal life in the shallow subseafloor crust at deep-sea hydrothermal vents
    # Physics
    "10.1038/s41467-024-49689-w", #* Amplification of electromagnetic fields by a rotating body
    "10.1038/s41467-024-48575-9", #* Zero-shot learning enables instant denoising and super-resolution in optical fluorescence microscopy
    "10.1038/s41467-024-45586-4", #* Current-induced switching of a van der Waals ferromagnet at room temperature
    "10.1038/s41467-024-46372-y", #* Ultra-fast switching memristors based on two-dimensional materials
    # "10.1038/s41467-024-45888-7", # General-purpose programmable photonic processor for advanced radiofrequency applications
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

# run articles3[0] from hebrew onward, run 1-2 from German onward

# model = Qwen()
model = Llama()
# model = GPT()
tl = Translator(model)
tl.use_context = True
languages = languages2[1:]
# languages = [l for l in languages2 if l != 'Spanish']
# languages = [l for l in load_langs()['translation'].keys() if l != 'Slovene']#[-6:]
# languages = languages[languages.index("Farsi"):]
# languages = ["Chinese (simplified characters)","Bengali","Urdu","Marathi","Tamil","Telugu","Gujarati"]#, "Chinese (traditional characters)", "Japanese"]
j = 0
for i,doi in enumerate(articles3[:2]):

    data = get_nature_article(doi)
    if tl.use_context:
        fulltext_dir = f"FullTexts/{filename_from_DOI(doi=doi)}"
        fulltext_path = f"{fulltext_dir}/eng_full.txt"
        if not os.path.isdir(fulltext_dir):
            os.mkdir(fulltext_dir)
        if not os.path.isfile(fulltext_path):
            save_fulltext(get_copy(data), f"FullTexts/{filename_from_DOI(doi=doi)}/eng_full.txt")
        
        tl.load_article(fulltext_path)
        # print(tl.context)

    t = time.time()
    print(doi, f'(index = {i+j})')
    for lang in languages:
        print(lang)
        this_data = get_copy(data)

        if lang != "English":
            translate_article(this_data, tl, lang)
            print(f"{lang}: {tl.model.count_tokens()}")

        add_mathML(this_data)
        change_graphic_dir(this_data)

        # SAVING
        doi_name = filename_from_DOI(doi=doi)
        folder_path = f"articles/{doi_name}"
        if not os.path.isdir(folder_path):
            os.mkdir(folder_path)
        
        if lang == 'English':
            xml_name = 'eng.xml'
        else: # helps me generate files from diff model translations without resaving the same english file under diff names.
            xml_name = f"{load_langs()['translation'][lang]}_llama.xml"

        f = open(f"{folder_path}/{xml_name}", "w")    
        f.write(this_data.prettify())
        f.close()
        total_tokens, input_tokens = model.count_tokens()
        # f = open(f"{folder_path}/tokens.txt","w")
        # f.write(f"input: {input_tokens}\noutput: {total_tokens-input_tokens}\ntotal: {total_tokens}\narticle: {tl.article_tokens}")
        # f.close()

        # ADD THIS ARTICLE TO THE CATALOG.

        tl.reset()


    t = time.time() - t
    print(doi, f'done. (index = {i+j})')
    print(f"{len(languages)} language(s) took {round(t/60)} minutes.")

    # Update catalog.
    # tools.update_dropdown_langs(languages)

    tools.update_catalog([doi_name])
    tools.update_index_files(languages)