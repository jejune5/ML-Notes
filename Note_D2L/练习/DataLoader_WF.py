import collections


def read_WangFen():
    with open('../../data/汪峰.txt','r',encoding='utf-8') as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines]
        return lines



def tokenize(lines, token='word'):
    return [list(line) for line in lines]


def count_corpus(tokens):
    if len(tokens) == 0 or isinstance(tokens[0], list):
        tokens = [token for line in tokens for token in line]
        return collections.Counter(tokens)



class Vocab:
    def __init__(
        self,
        tokens = None,
        min_freq = 0,
        reserved_token=None
    ):
        if tokens is None:
            tokens = []
        if reserved_token is None:
            reserved_token = []

        counter = count_corpus(tokens=tokens)
        self._token_freqs = sorted(counter.items(), key=lambda x: x[1], reverse=True)

        self.idx_to_token = ['<unk>'] + reserved_token
        self.token_to_idx = {token: idx
            for idx, token in enumerate(self.idx_to_token)}
        for token, freq in self._token_freqs:
            if freq < min_freq:
                break
            if token not in self.token_to_idx:
                self.idx_to_token.append(token)
                self.token_to_idx[token] = len(self.idx_to_token) - 1
    
    def __len__(self):
        return len(self.idx_to_token)
    
    def __getitem__(self, tokens):
        if not isinstance(tokens,(list, tuple)):
            return self.token_to_idx.get(tokens, self.unk)
        return [self.__getitem__(token) for token in tokens]

    def to_tokens(self, indices):
        if not isinstance(indices, (list, tuple)):
            return self.idx_to_token[indices]
        return [self.idx_to_token[index] for index in indices]

    @property
    def unk(self):
        return 0

    @property
    def token_freqs(self):
        return self._token_freqs


def load_corpus(max_tokens=-1):
    lines = read_WangFen()
    tokens = tokenize(lines=lines)
    vocab = Vocab(tokens=tokens)
    corpus = [vocab[token] for token in tokens]
    if max_tokens > 0:
        corpus = corpus[:max_tokens]
    return corpus, vocab
