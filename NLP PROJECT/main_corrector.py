import re

class SimpleCorrector:
    def __init__(self):
        # Load a large list of English words
        try:
            with open('words.txt', 'r', encoding='utf-8') as f:
                self.words = set(word.strip().lower() for word in f if word.strip())
        except FileNotFoundError:
            print("Error: words.txt not found. Please ensure it's in the same directory.")
            print("You can get a large word list from: https://raw.githubusercontent.com/dwyl/english-words/master/words.txt")
            self.words = set() # Initialize an empty set to prevent errors
        
    def correct_text(self, text):
        words = text.split()
        corrected_words = []
        for word in words:
            clean_word = re.sub(r'[^\w\s]', '', word.lower())
            if not clean_word:
                corrected_words.append(word)
                continue
            if clean_word in self.words:
                corrected_words.append(word)
                continue
            suggestion = self._get_best_match(clean_word)
            # Preserve original capitalization
            if word.istitle():
                suggestion = suggestion.title()
            elif word.isupper():
                suggestion = suggestion.upper()
            corrected_words.append(suggestion)
        return ' '.join(corrected_words)
    
    def _get_best_match(self, word):
        # Find the closest word in the dictionary by edit distance
        min_dist = float('inf')
        best_word = word
        if not self.words: # Handle case where words.txt was not loaded
            return word
        for w in self.words:
            dist = self._levenshtein(word, w)
            if dist < min_dist:
                min_dist = dist
                best_word = w
            if min_dist == 1:  # Early stop for very close match
                break
        return best_word

    def _levenshtein(self, s1, s2):
        if len(s1) < len(s2):
            return self._levenshtein(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

if __name__ == "__main__":
    # Create an instance of SimpleCorrector
    corrector = SimpleCorrector()

    if not corrector.words:
        print("Exiting because the word list could not be loaded.")
    else:
        # Prompt the user for input text
        user_text = input("Enter text to correct: ")

        # Print the original and corrected text
        print("Original text:", user_text)
        print("Corrected text:", corrector.correct_text(user_text)) 