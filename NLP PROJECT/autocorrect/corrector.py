import re
import string
from collections import Counter
import nltk
from nltk.util import ngrams
from nltk.tokenize import word_tokenize
from nltk.corpus import words as nltk_words
# Removed TextBlob and SymSpell dependencies
from spellchecker import SpellChecker

class Corrector:
    def __init__(self, custom_dict_path=None, max_edit_distance=2):
        # Download NLTK resources if not already downloaded
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
            
        try:
            nltk.data.find('corpora/words')
        except LookupError:
            nltk.download('words')
        
        # Initialize dictionary
        self.dictionary = set(nltk_words.words())
        self.word_freq = Counter()
        
        # Load custom dictionary if provided
        if custom_dict_path:
            self.load_custom_dictionary(custom_dict_path)
        
        # Initialize SpellChecker
        self.spell_checker = SpellChecker()
        
        # Keep track of user corrections for personalized suggestions
        self.user_corrections = {}
        
    def load_custom_dictionary(self, file_path):
        """Load custom dictionary and word frequencies from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        word = parts[0].lower()
                        freq = int(parts[1])
                        self.dictionary.add(word)
                        self.word_freq[word] = freq
        except Exception as e:
            print(f"Error loading custom dictionary: {e}")
    
    def _tokenize(self, text):
        """Tokenize text into words"""
        return word_tokenize(text.lower())
    
    def _preprocess(self, text):
        """Preprocess text by removing special characters and normalizing"""
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation from the end of words but keep internal punctuation
        text = re.sub(r'([a-z])([^\w\s])\s', r'\1 ', text)
        return text
    
    def _calculate_levenshtein_distance(self, word1, word2):
        """Calculate the Levenshtein (edit) distance between two words"""
        if len(word1) < len(word2):
            return self._calculate_levenshtein_distance(word2, word1)
        
        if len(word2) == 0:
            return len(word1)
        
        previous_row = range(len(word2) + 1)
        for i, c1 in enumerate(word1):
            current_row = [i + 1]
            for j, c2 in enumerate(word2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _get_candidates(self, word, max_distance=2):
        """Generate candidate corrections for a word using edit distance"""
        # Return the word if it's in the dictionary
        if word in self.dictionary:
            return [word]
        
        # Generate candidates with edit distance <= max_distance
        candidates = []
        for dict_word in self.dictionary:
            distance = self._calculate_levenshtein_distance(word, dict_word)
            if distance <= max_distance:
                candidates.append((dict_word, distance))
        
        # Sort by edit distance and then by frequency
        candidates.sort(key=lambda x: (x[1], -self.word_freq.get(x[0], 0)))
        return [word for word, _ in candidates]
    
    def _get_norvig_candidates(self, word, max_distance=2):
        """Generate candidates using Norvig's algorithm (with edits)"""
        def edits1(word):
            """All edits that are one edit away from word"""
            letters = string.ascii_lowercase
            splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
            deletes = [L + R[1:] for L, R in splits if R]
            transposes = [L + R[1] + R[0] + R[2:] for L, R in splits if len(R) > 1]
            replaces = [L + c + R[1:] for L, R in splits if R for c in letters]
            inserts = [L + c + R for L, R in splits for c in letters]
            return set(deletes + transposes + replaces + inserts)
        
        def edits2(word):
            """All edits that are two edits away from word"""
            return set(e2 for e1 in edits1(word) for e2 in edits1(e1))
        
        # Known edits
        candidates = set()
        if max_distance >= 1:
            candidates.update(e for e in edits1(word) if e in self.dictionary)
        if max_distance >= 2:
            if not candidates:
                candidates.update(e for e in edits2(word) if e in self.dictionary)
        
        # Add original word if it's in dictionary
        if word in self.dictionary:
            candidates.add(word)
            
        # Sort by frequency
        candidates = list(candidates)
        candidates.sort(key=lambda x: self.word_freq.get(x, 0), reverse=True)
        
        return candidates if candidates else [word]
    
    def correct_word(self, word):
        """Correct a single word using multiple methods and return best suggestion"""
        if not word or word.strip() == "":
            return word
            
        # Normalize word
        word = word.lower().strip()
        
        # If word is in dictionary, return it
        if word in self.dictionary:
            return word
            
        # Check user corrections first
        if word in self.user_corrections:
            return self.user_corrections[word]
        
        # Method 1: Use SpellChecker (based on Peter Norvig's algorithm)
        norvig_correction = self.spell_checker.correction(word)
        
        # Method 2: Use our custom Levenshtein implementation
        levenshtein_candidates = self._get_candidates(word)
        levenshtein_correction = levenshtein_candidates[0] if levenshtein_candidates else word
        
        # Method 3: Use Norvig's algorithm directly
        norvig_candidates = self._get_norvig_candidates(word)
        norvig_direct_correction = norvig_candidates[0] if norvig_candidates else word
        
        # Voting system: choose the most common correction
        corrections = [
            norvig_correction or word, 
            levenshtein_correction, 
            norvig_direct_correction
        ]
        
        correction_counter = Counter(corrections)
        best_correction, count = correction_counter.most_common(1)[0]
        
        return best_correction
    
    def correct_text(self, text):
        """Correct all misspelled words in a text"""
        if not text:
            return text
            
        # Preprocess text
        preprocessed_text = self._preprocess(text)
        
        # Tokenize into words
        tokens = self._tokenize(preprocessed_text)
        
        # Keep track of original word positions and punctuation
        corrected_tokens = []
        for token in tokens:
            # Skip punctuation and numbers
            if token in string.punctuation or token.isdigit():
                corrected_tokens.append(token)
                continue
            
            # Correct the word
            corrected = self.correct_word(token)
            corrected_tokens.append(corrected)
        
        # Join tokens back into text
        corrected_text = ' '.join(corrected_tokens)
        
        # Fix spacing around punctuation
        corrected_text = re.sub(r'\s+([,.!?:;])', r'\1', corrected_text)
        
        return corrected_text
    
    def correct_with_context(self, text):
        """Correct text considering n-gram context"""
        if not text:
            return text
            
        # Preprocess text
        preprocessed_text = self._preprocess(text)
        
        # Tokenize into words
        tokens = self._tokenize(preprocessed_text)
        
        # Correct tokens considering context
        corrected_tokens = list(tokens)  # Create a copy
        
        # Process tokens with context
        for i in range(len(tokens)):
            token = tokens[i]
            
            # Skip punctuation and numbers
            if token in string.punctuation or token.isdigit():
                continue
                
            # If token is in dictionary, continue
            if token in self.dictionary:
                continue
                
            # Get correction candidates
            candidates = self._get_candidates(token)
            if not candidates or candidates[0] == token:
                candidates = self._get_norvig_candidates(token)
            
            if not candidates or len(candidates) == 1:
                corrected_tokens[i] = self.correct_word(token)
                continue
                
            # Consider context using n-grams if we have multiple candidates
            best_candidate = token
            highest_score = -1
            
            # Get context (previous and next words)
            context_before = tokens[max(0, i-2):i]
            context_after = tokens[i+1:min(len(tokens), i+3)]
            
            # Score each candidate based on n-gram probability
            for candidate in candidates:
                score = 0
                
                # Check bigrams with previous word
                if context_before:
                    bigram = ' '.join([context_before[-1], candidate])
                    # Simple scoring based on whether we've seen this bigram
                    if bigram in self.word_freq:
                        score += self.word_freq[bigram]
                    
                # Check bigrams with next word
                if context_after:
                    bigram = ' '.join([candidate, context_after[0]])
                    if bigram in self.word_freq:
                        score += self.word_freq[bigram]
                
                # If this candidate has a higher score, update best candidate
                if score > highest_score:
                    highest_score = score
                    best_candidate = candidate
            
            # If no good context match, fall back to basic correction
            if highest_score <= 0:
                corrected_tokens[i] = self.correct_word(token)
            else:
                corrected_tokens[i] = best_candidate
        
        # Join tokens back into text
        corrected_text = ' '.join(corrected_tokens)
        
        # Fix spacing around punctuation
        corrected_text = re.sub(r'\s+([,.!?:;])', r'\1', corrected_text)
        
        return corrected_text
    
    def add_to_dictionary(self, word, frequency=1):
        """Add a word to the custom dictionary"""
        word = word.lower().strip()
        self.dictionary.add(word)
        self.word_freq[word] = frequency
        self.spell_checker.word_frequency.add(word)
    
    def add_user_correction(self, misspelled_word, correction):
        """Add a user-specific correction to improve personalized suggestions"""
        misspelled_word = misspelled_word.lower().strip()
        correction = correction.lower().strip()
        self.user_corrections[misspelled_word] = correction
        
        # Also add the correction to dictionary if not already there
        if correction not in self.dictionary:
            self.add_to_dictionary(correction) 