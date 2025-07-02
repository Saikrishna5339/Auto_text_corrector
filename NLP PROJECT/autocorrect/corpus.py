import os
import re
import string
from collections import Counter
import nltk
from nltk.corpus import brown
import pandas as pd
import numpy as np

class CorpusHandler:
    def __init__(self, corpus_path=None):
        # Download NLTK resources if not already downloaded
        try:
            nltk.data.find('corpora/brown')
        except LookupError:
            nltk.download('brown')
        
        # Initialize word frequency Counter
        self.word_freq = Counter()
        self.bigram_freq = Counter()
        
        # Load default NLTK corpus if no custom corpus provided
        if not corpus_path:
            self._load_nltk_corpus()
        else:
            self.load_custom_corpus(corpus_path)
    
    def _load_nltk_corpus(self):
        """Load word frequencies from the Brown corpus"""
        words = brown.words()
        
        # Count word frequencies
        for word in words:
            word = word.lower()
            if word.isalpha():  # Only consider alphabet words
                self.word_freq[word] += 1
        
        # Count bigram frequencies
        bigrams = nltk.bigrams([w.lower() for w in words if w.isalpha()])
        for bg in bigrams:
            self.bigram_freq[' '.join(bg)] += 1
    
    def load_custom_corpus(self, file_path):
        """Load a custom corpus from a text file"""
        try:
            # Check file type
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read().lower()
                    
                    # Remove special characters and normalize
                    text = re.sub(r'[^\w\s]', ' ', text)
                    
                    # Tokenize
                    words = text.split()
                    
                    # Count word frequencies
                    for word in words:
                        if word.isalpha():
                            self.word_freq[word] += 1
                    
                    # Count bigram frequencies
                    bigrams = nltk.bigrams([w for w in words if w.isalpha()])
                    for bg in bigrams:
                        self.bigram_freq[' '.join(bg)] += 1
            
            elif ext in ['.csv', '.xlsx', '.xls']:
                # Load structured data
                if ext == '.csv':
                    df = pd.read_csv(file_path)
                else:
                    df = pd.read_excel(file_path)
                
                # Assume the data has 'word' and 'frequency' columns
                if 'word' in df.columns and 'frequency' in df.columns:
                    for _, row in df.iterrows():
                        word = str(row['word']).lower()
                        freq = int(row['frequency'])
                        if word.isalpha():
                            self.word_freq[word] = freq
                else:
                    # If not structured, process all text in the dataframe
                    for col in df.columns:
                        for item in df[col]:
                            if isinstance(item, str):
                                words = re.sub(r'[^\w\s]', ' ', item.lower()).split()
                                for word in words:
                                    if word.isalpha():
                                        self.word_freq[word] += 1
            
            else:
                print(f"Unsupported file type: {ext}")
                
        except Exception as e:
            print(f"Error loading custom corpus: {e}")
    
    def export_word_frequencies(self, output_path):
        """Export word frequencies to a file"""
        try:
            # Sort by frequency
            sorted_words = sorted(self.word_freq.items(), key=lambda x: x[1], reverse=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for word, freq in sorted_words:
                    f.write(f"{word} {freq}\n")
                    
            print(f"Word frequencies exported to {output_path}")
            
        except Exception as e:
            print(f"Error exporting word frequencies: {e}")
    
    def get_top_words(self, n=1000):
        """Get the top n most frequent words"""
        return dict(self.word_freq.most_common(n))
    
    def get_word_frequency(self, word):
        """Get the frequency of a specific word"""
        return self.word_freq.get(word.lower(), 0)
    
    def get_bigram_frequency(self, word1, word2):
        """Get the frequency of a specific bigram"""
        bigram = f"{word1.lower()} {word2.lower()}"
        return self.bigram_freq.get(bigram, 0)
    
    def get_relative_frequency(self, word):
        """Get the relative frequency of a word (0-1 scale)"""
        if not self.word_freq:
            return 0
            
        total_words = sum(self.word_freq.values())
        return self.word_freq.get(word.lower(), 0) / total_words if total_words > 0 else 0
    
    def generate_confusion_set(self, n=1000):
        """Generate a confusion set of commonly misspelled words"""
        confusion_set = {}
        
        # Common misspelling patterns
        patterns = [
            ('ei', 'ie'),  # receive vs recieve
            ('a', 'e'),    # dependent vs dependant
            ('e', 'a'),    # separate vs separate
            ('ant', 'ent'), # assistant vs assistent
            ('ent', 'ant'), # persistent vs persistant
            ('ce', 'se'),  # advice vs advise
            ('se', 'ce'),  # license vs licence
            ('able', 'ible'), # dependable vs dependible
            ('ible', 'able'), # compatible vs compatable
            ('ary', 'ery'), # dictionary vs dictionery
            ('ery', 'ary'), # cemetery vs cemetary
            ('er', 'or'),  # adapter vs adaptor
            ('or', 'er'),  # professor vs professer
            ('mm', 'm'),   # accommodate vs acommodate
            ('m', 'mm'),   # commitment vs committment
            ('ll', 'l'),   # parallel vs paralel
            ('l', 'll'),   # until vs untill
            ('cc', 'c'),   # occasion vs ocassion
            ('c', 'cc'),   # occasion vs ocassion
            ('ss', 's'),   # possession vs posession
            ('s', 'ss'),   # desert vs dessert
            ('tion', 'sion'), # attention vs attension
            ('sion', 'tion'), # extension vs extention
        ]
        
        # Get top words to create confusion set
        top_words = list(self.get_top_words(n).keys())
        
        for word in top_words:
            if len(word) <= 3:  # Skip very short words
                continue
                
            for orig, repl in patterns:
                if orig in word:
                    misspelled = word.replace(orig, repl)
                    if misspelled not in top_words:  # Only if misspelling is not a valid word
                        confusion_set[misspelled] = word
        
        return confusion_set 