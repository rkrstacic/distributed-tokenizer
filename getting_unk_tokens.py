import json
import re

from nltk.stem import WordNetLemmatizer
from tokenization import FullTokenizer
from collections import Counter


class SaveUnknownTokensService:
    unknown_tokens = []
    tokenized_counter = None
    clean_token_difference = []
    small_tokens_wildcards = []

    def __init__(self, vocab_file: str, small_vocab_file):
        self.vocab_file = vocab_file
        self.small_vocab_file = small_vocab_file
        self.full_tokenizer = FullTokenizer(vocab_file, True)

    @staticmethod
    def lemmatize(word):
        wnl = WordNetLemmatizer()
        wnl.lemmatize(wnl.lemmatize(word, pos="n"), pos="v")

    def tokenize_corpus(self, corpus: str):
        self.tokenized_counter = Counter(self.full_tokenizer.tokenize(corpus))

    def save_small_vocab(self):
        with open(self.small_vocab_file, 'w') as fs:
            fs.write("\n".join(key for key, value in self.tokenized_counter))

    def prepare_tokens(self):
        all_tokens = self.tokenized_counter.keys()
        all_tokens = list(self.lemmatize(token) for token in all_tokens)

        small_tokens = self.tokenized_counter.most_common(500)
        small_tokens = list(self.lemmatize(key) for key, value in small_tokens)

        difference = set(all_tokens) - set(small_tokens)
        self.clean_token_difference = list(i for i in difference if "#" not in i)

        small_tokens_wildcards = [token for token in list(small_tokens) if "#" in token]
        self.small_tokens_wildcards = list(i for i in small_tokens_wildcards if i not in [".", "^", "|"])

    def find_unknown_tokens(self):
        potential_unknown_tokens = []
        for clean_token in self.clean_token_difference:
            for wildcard_token in self.small_tokens_wildcards:
                try:
                    if re.match(wildcard_token.replace("#", ".") + r"\b", clean_token) is not None:
                        break
                except:
                    pass
            else:
                potential_unknown_tokens.append(clean_token)

        small_tokenizer = FullTokenizer(self.small_vocab_file, True)
        unknown_tokens = list(
            [i, small_tokenizer.tokenize(i)] for i in potential_unknown_tokens if "[UNK]" in small_tokenizer.tokenize(i)
        )

        alnum_unknown_tokens = list([i[0] for i in sorted(unknown_tokens) if i[0].isalnum()])
        self.unknown_tokens = [token for token in alnum_unknown_tokens if not any(char.isdigit() for char in token)]

    def save_unknown_tokens(self, file: str):
        with open(file, 'w') as f:
            f.write("\n".join(self.unknown_tokens))


if __name__ == '__main__':
    with open("nba.txt") as n, open("politics.txt") as p:
        nba_comments = " ".join(json.loads(row)["comment"] for row in n)
        politics_comments = " ".join(json.loads(row)["comment"] for row in p)

    service = SaveUnknownTokensService("vocab.txt", "small_vocab.txt")
    service.tokenize_corpus(nba_comments + ' ' + politics_comments)
    # service.save_small_vocab()
    service.prepare_tokens()
    service.find_unknown_tokens()
    service.save_unknown_tokens("unknown_tokens.txt")
