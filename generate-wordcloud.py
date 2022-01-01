import json
import argparse
import re
from functools import reduce
from janome.tokenizer import Tokenizer
from tqdm import tqdm
from wordcloud import WordCloud

parser = argparse.ArgumentParser()
parser.add_argument("input")
parser.add_argument("output")
parser.add_argument("-f", "--font", default="/library/Fonts/FOT-BabyPopStd-EB.otf")
args = parser.parse_args()

# read a variable
with open(args.input) as fp:
    text = fp.read().split("\n")
text = "[" + "\n".join(text[1:])

enable_sources = ["Twitter Web", "Twitter for", "TweetDeck"]
except_parts_of_speech = ["助詞", "助動詞"]
except_words = ["する", "なる", "てる", "ある", "の", "いる", "れる", "そう"]
mention_pattern = re.compile(r"@[a-zA-Z0-9_]+")
url_pattern = re.compile(r"https?://[a-zA-Z0-9-_./]+")
json_data = json.loads(text)
tokenizer = Tokenizer()

base_form_lexicon = ""
collocation_lexicon = ""

for item in tqdm(json_data):
    # filter
    tweet = item["tweet"]
    enables_source = reduce(lambda previous, source: source in tweet["source"] or previous, enable_sources, False)
    retweeted = tweet["full_text"].startswith("RT @")
    is2021 = tweet["created_at"].endswith("2021")
    if not enables_source or retweeted or not is2021:
        continue

    # remove URLs and mentions
    text = tweet["full_text"]
    text = mention_pattern.sub("", text)
    text = url_pattern.sub("", text)
    text += " "

    # morphological analysis
    last_word = ""
    last_part_of_speech = None

    filter_word = lambda word: len(word) > 1 and word not in except_words

    for token in tokenizer.tokenize(text):
        part_of_speech = token.part_of_speech.split(",")[0]
        if part_of_speech not in except_parts_of_speech:
            if last_part_of_speech == None or last_part_of_speech == part_of_speech:
                last_word += token.surface
            else:
                if filter_word(last_word):
                    collocation_lexicon += last_word + " "
                last_word = ""
            if filter_word(token.base_form):
                base_form_lexicon += token.base_form + " "
        last_part_of_speech = part_of_speech
    if filter_word(last_word):
        collocation_lexicon += last_word + " "

wc = WordCloud(width=1920, height=1080, font_path=args.font, background_color="#fff")
wc.generate(base_form_lexicon + " " + collocation_lexicon)
wc.to_file(args.output)