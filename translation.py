from openai import OpenAI
import tiktoken
from typing import Union as u
import os
import base64
from io import BytesIO
from PIL import Image
from google.cloud import translate_v2 as gtrans
import time

class Translator():
  def __init__(self, model):
    self.name = model
    if model == "gpt":
      self.model = "gpt-4o-2024-08-06"
      # self.model = "gpt-4o-mini-2024-07-18"
      self.max_tokens = 16384
      self.api_key_location = "../keys/openai_key.txt"
      self.use_tokens = True
      self.client = OpenAI(api_key=self.api_key())
    elif model == "llama":
      self.model = "llama3.1-405b"
      self.max_tokens = 4096
      self.api_key_location = "../keys/llama_key.txt"
      self.use_tokens = False
      self.client = OpenAI(api_key=self.api_key(), base_url="https://api.llama-api.com")
    else:
      raise ValueError('Invalid model. Available models: "gpt", "llama".')

    if self.use_tokens:
      self.encoding = tiktoken.encoding_for_model(self.model)
    self.token_count = 0
    self.context = ""
    self.use_context = False
    self.use_example = False # give model an example translation with technical terms preserved in English.
    self.temp = 0
    self.images = [] # image encodings
    self.reset()

  def clear_tokens(self):
    self.token_count = 0

  def reset(self):
    self.first = True
    self.saved_convo = [
      {"role": "system", "content": "You are a translator for scientific articles."}
    ]
    self.images = []
    self.clear_tokens()

  def count_tokens(self):
    return self.token_count
  
  def _load_text(self, path):
    with open(path, "r") as f:
      try:
        lines = f.readlines()
        return ''.join(lines)
      except:
        print("Article not found!")

  def load_article(self, path):
    self.context = self._load_text(path)

  def load_example(self):
    example_path = "sample.txt"
    txt = self._load_text(example_path)

    og_txt, trans_txt = txt[:txt.find('\n')], txt[txt.find('\n')+2:]

    prompt = f"Here is an excerpt of a scientific article: \n\n{og_txt}\n\nPlease take note of any highly domain specific words in this excerpt. Then, please translate the excerpt into Korean. But do not translate those highly domain specific words that you identified. For those words, keep the original English words in your translation instead. Everything else in the excerpt should be translated into Korean."
    # Of these, only keep note of those terms which are the most technical and unique. 
    # print(prompt)
    # print(trans_txt)
    self.saved_convo = [{"role": "user", "content": f"{prompt}"},
                        {"role": "assistant", "content": f"{trans_txt}"}]

  def prompt_get_json(self, prompt, figs=False):
    print("prompting...")
    if figs:
      response = self.chat_prompt_with_figures(text_prompt=prompt)
    else:
      response = self.chat_prompt(prompt)
    print(response)
    i = response.find("{") # start of the xml object
    j = response.rindex("}")+1 # end of the xml object
    return response[i:j]

  def get_name_from_xml(self, xmlstring):
    a = xmlstring
    try:
      header = a[a.find("<"):a.find(">")]
      if header.find(" ") != -1:
        return header[1:header.find(" ")]
      else:
        return header[1:]
    except:
      return "nothing"

  def api_key(self):
    # read api_key from local file
    with open(self.api_key_location) as f:
      return f.readline()
  
  def num_tokens(self, text):
    # returns the number of tokens that corresponds to the text
    if self.use_tokens:
      return len(self.encoding.encode(text))
    else:
      return 0
    
  def upload_images(self, doi):
    img_folder = f"MediaObjects/{doi}/"
    try:
      img_files = [img_folder+fn for fn in os.listdir(img_folder) if fn[-3:] == "png" or fn[-3:] == "jpg"]
    except:
      print("No figures.")
      return []
    
    img_encodings = []

    for img_path in img_files:
        with Image.open(img_path) as img:
            width, height = img.size
            max_dim = max(width, height)
            if max_dim > 512:
                scale_factor = 512 / max_dim
                new_width = int(width * scale_factor)
                new_height = int(height * scale_factor)
                img = img.resize((new_width, new_height))

            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
            img_encodings.append(img_str)
    
    self.images = img_encodings

  def chat_prompt(self, prompt, printing=True):
    # returns the result of a GPT chat prompt
    response = self.client.chat.completions.create(
      model=self.model,
      temperature=self.temp,
      messages=self.saved_convo + [{"role": "user", "content": prompt}],
      max_tokens=self.max_tokens
    )
    print(self.saved_convo + [{"role": "user", "content": prompt}])
    ret = response.choices[0].message.content

    token_price = sum([self.num_tokens(prompt), self.num_tokens(ret)] + [self.num_tokens(d["content"]) for d in self.saved_convo])
    if printing:
      print(f"Exchange complete. Price: {token_price} tokens.")
    self.token_count += token_price
    return ret
  
  def chat_prompt_with_figures(self, text_prompt, doi=None):
    if doi: # doi has to be the formatted doi
      self.upload_images(doi)

    text_count = ""+text_prompt
    messages = self.saved_convo + [
        {
          "role": "user", "content":
            [
              {"type": "text", "text": text_prompt}
            ]
        }
      ]
    for img in self.images:
      img_prompt = {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}}
      messages[1]["content"].append(img_prompt)
      text_count += img
    # print(self.images)


    response = self.client.chat.completions.create(
      model=self.model,
      temperature=self.temp,
      messages=messages
      )
    ret = response.choices[0].message.content

    token_price = sum([self.num_tokens(text_count), self.num_tokens(ret)] + [self.num_tokens(d["content"]) for d in self.saved_convo])
    print(f"Exchange complete. Price: {token_price} tokens.")
    self.token_count += token_price
    return ret

  def translate_text(self, text, language, prompt=None):
    # returns the translation of bare text into any language.
    # returns a list of translations or single translation.

    # prompt = f"The following phrase is an exerpt from a scientific article. If this phrase is in {language} already, just return the sentence without changing it. Otherwise, please translate the phrase into {language}: {text}"
    if not prompt:
      prompt = f"Please translate the following scientific excerpt into {language}."
      if self.use_example:
        prompt = "Perfect! Now, here is a different excerpt. Again, please take note of any highly domain specific words in this excerpt. Then, "+prompt+f" But do not translate those highly domain specific words that you identified. For those words, keep the original English words in your translation instead. Everything else in the excerpt should be translated into {language}. Print the list of words you decided to keep in English, then print the translation. \n\n"
        # Of these, only keep note of those terms which are the most technical/unique. 
      prompt += "\n\n"

    if isinstance(text, list):
      res = []
      count = self.token_count
      for t in text:
        res.append(self.chat_prompt(prompt+t, printing=False))
        time.sleep(0.05)
      count = self.token_count - count
      print(f"{language}: {count} tokens.")
      return res
    else: # single translation
      return self.chat_prompt(prompt+text)

  def translate_xml(self, xml: u[str,list], language):
    # returns the (string of) an xml object or list of xml objects after translating its contents into any language.
    intro, outro = "", ""
    is_list = isinstance(xml, list)
    if is_list:
      num_xml = len(xml)
      intro += f"This following Python list contains {num_xml} sections of a scientific article, each section represented by an xml object. For each of the {num_xml} xml objects,"
      outro += f"The format of the response must be a Python list of length {num_xml}, where each element is the translated xml object. Here is the list:"
    else: # single xml.
      intro += "The following xml object represents a section of a scientific article. For the entire section,"
      outro += "The format of the response should be the translated xml object. Here is the object:"
      
    instructions = f"please translate all content between tags into {language}. Please keep all of the xml tags in the correct positions. Do not omit any section of the xml. Do not translate the word 'Fig'. Do not cut sentences short and include all symbols."
    if self.use_context:
      if self.first:
        prompt = f"In the next messages, you will receive sections of a scientific article to translate into {language}. Here is the full scientific article; please use this as context to help the translation. The article: {self.context}"
        self.saved_convo += [{"role": "user", "content": f"{prompt}"},
                            {"role": "assistant", "content": f"{self.chat_prompt(prompt)}"}]
        self.first = False
      prompt = f"Thank you. {intro} {instructions} Please use the entire article provided earlier for context. {outro} {xml}"
    else:
      prompt = f"{intro} {instructions} {outro} {xml}"
    
    response = self.chat_prompt(prompt)

    if not is_list:
      i = response.find("<") # start of the xml object
      j = response.rindex(">")+1 # end of the xml object
      return response[i:j]
    else:
      translated = []
      a, currname = response, self.get_name_from_xml(response)
      
      while a.find(f"</{currname}>") != -1:
          k = a.find("<")
          l = a.find(f"</{currname}>") + len(f"</{currname}>")
          translated.append(a[k:l])
          a = a[l:]
          currname = self.get_name_from_xml(a)

      print(len(translated))
      # print(translated)
      return translated
    


class GoogleTranslator():
  ISO_dict = {
      "English": "en",
      "Chinese (simplified characters)": "zh-CN",
      "Chinese (traditional characters)": "zh-TW",
      "German": "de",
      "Japanese": "ja",
      "French": "fr",
      "Korean": "ko",
      "Hindi": "hi",
      "Bengali": "bn",
      "Urdu": "ur",
      "Marathi": "mr",
      "Tamil": "ta",
      "Telugu": "te",
      "Gujarati": "gu",
      "Italian": "it",
      "Spanish": "es",
      "Dutch": "nl",
      "Swedish": "sv",
      "Danish": "da",
      "Hebrew": "iw",
      "Malay": "ms",
      "Serbian": "sr",
      "Portuguese": "pt",
      "Turkish": "tr",
      "Russian": "ru",
      "Arabic": "ar",
      "Farsi": "fa",
      "Swahili": "sw",
      "Vietnamese": "vi"
    }
  
  def __init__(self):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"../keys/googletrans_key.json"
    self.client = gtrans.Client()
  
  def translate(self, txt, lang):
    res = self.client.translate(txt,
                                target_language=self.ISO(lang),
                                source_language="en")
    if isinstance(res, list):
      return [r['input'] for r in res], [r['translatedText'] for r in res]
    else:
      return res['input'], res['translatedText']
  
  def ISO(self, lang):
    return self.ISO_dict[lang]
  