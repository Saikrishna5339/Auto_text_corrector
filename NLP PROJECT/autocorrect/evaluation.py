import time
import random
import string
from collections import Counter

class SpellCheckerEvaluator:
    def __init__(self, corrector, corpus_handler=None):
        """Initialize the evaluator with a corrector and optional corpus"""
        self.corrector = corrector
        self.corpus_handler = corpus_handler
        self.results = {
            'accuracy': 0,
            'precision': 0,
            'recall': 0,
            'f1_score': 0,
            'avg_time_per_word': 0,
            'avg_time_per_text': 0
        }
    
    def _generate_misspellings(self, word, num_errors=1):
        """Generate misspelled versions of a word"""
        if len(word) <= 1:
            return word
            
        word = word.lower()
        chars = list(word)
        
        # Define error types
        error_types = ['insertion', 'deletion', 'substitution', 'transposition']
        
        for _ in range(min(num_errors, len(word))):
            error_type = random.choice(error_types)
            
            if error_type == 'insertion':
                # Insert a random character
                pos = random.randint(0, len(chars))
                chars.insert(pos, random.choice(string.ascii_lowercase))
                
            elif error_type == 'deletion' and len(chars) > 1:
                # Delete a random character
                pos = random.randint(0, len(chars) - 1)
                chars.pop(pos)
                
            elif error_type == 'substitution':
                # Substitute a character with a random one
                pos = random.randint(0, len(chars) - 1)
                chars[pos] = random.choice(string.ascii_lowercase.replace(chars[pos], ''))
                
            elif error_type == 'transposition' and len(chars) > 1:
                # Swap two adjacent characters
                pos = random.randint(0, len(chars) - 2)
                chars[pos], chars[pos + 1] = chars[pos + 1], chars[pos]
        
        return ''.join(chars)
    
    def _generate_test_data(self, size=100, error_rate=0.3, max_errors_per_word=2):
        """Generate test data with misspelled words"""
        if not self.corpus_handler:
            raise ValueError("Corpus handler is required for generating test data")
            
        test_data = []
        words = list(self.corpus_handler.get_top_words(1000).keys())
        
        if not words:
            raise ValueError("No words available in corpus")
            
        for _ in range(size):
            original_word = random.choice(words)
            
            # Decide whether to introduce errors
            if random.random() < error_rate:
                num_errors = random.randint(1, max_errors_per_word)
                misspelled_word = self._generate_misspellings(original_word, num_errors)
            else:
                misspelled_word = original_word
                
            test_data.append((misspelled_word, original_word))
            
        return test_data
    
    def evaluate_word_correction(self, test_data=None, size=100):
        """Evaluate word correction performance"""
        if not test_data:
            test_data = self._generate_test_data(size=size)
            
        correct_predictions = 0
        true_positives = 0
        false_positives = 0
        false_negatives = 0
        total_time = 0
        
        for misspelled, original in test_data:
            # Skip if original and misspelled are the same
            if misspelled == original:
                continue
                
            start_time = time.time()
            prediction = self.corrector.correct_word(misspelled)
            total_time += time.time() - start_time
            
            # Accuracy
            if prediction.lower() == original.lower():
                correct_predictions += 1
                
            # Precision and recall metrics
            if misspelled != original:  # There was an actual error
                if prediction.lower() == original.lower():  # Correctly fixed
                    true_positives += 1
                else:  # Wrong correction
                    false_positives += 1
                    false_negatives += 1
                    
        # Calculate metrics
        total = len(test_data)
        accuracy = correct_predictions / total if total > 0 else 0
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        avg_time = total_time / total if total > 0 else 0
        
        self.results = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'avg_time_per_word': avg_time,
            'total_words': total,
            'correct_predictions': correct_predictions
        }
        
        return self.results
    
    def evaluate_text_correction(self, test_sentences=None, num_sentences=20, words_per_sentence=10, error_rate=0.3):
        """Evaluate text correction performance"""
        if not test_sentences:
            if not self.corpus_handler:
                raise ValueError("Corpus handler is required for generating test sentences")
                
            test_sentences = []
            words = list(self.corpus_handler.get_top_words(1000).keys())
            
            for _ in range(num_sentences):
                # Generate original sentence
                sentence_words = [random.choice(words) for _ in range(words_per_sentence)]
                original_sentence = ' '.join(sentence_words)
                
                # Create misspelled version
                misspelled_words = []
                for word in sentence_words:
                    if random.random() < error_rate:
                        misspelled_words.append(self._generate_misspellings(word))
                    else:
                        misspelled_words.append(word)
                        
                misspelled_sentence = ' '.join(misspelled_words)
                test_sentences.append((misspelled_sentence, original_sentence))
        
        total_accuracy = 0
        total_time = 0
        
        for misspelled_text, original_text in test_sentences:
            start_time = time.time()
            corrected_text = self.corrector.correct_with_context(misspelled_text)
            elapsed_time = time.time() - start_time
            total_time += elapsed_time
            
            # Calculate word-level accuracy
            original_words = original_text.lower().split()
            corrected_words = corrected_text.lower().split()
            
            # Ensure same length for comparison
            min_len = min(len(original_words), len(corrected_words))
            correct_words = sum(1 for i in range(min_len) if original_words[i] == corrected_words[i])
            
            accuracy = correct_words / len(original_words) if original_words else 1
            total_accuracy += accuracy
        
        avg_accuracy = total_accuracy / len(test_sentences) if test_sentences else 0
        avg_time = total_time / len(test_sentences) if test_sentences else 0
        
        self.results.update({
            'text_accuracy': avg_accuracy,
            'avg_time_per_text': avg_time,
            'num_texts': len(test_sentences)
        })
        
        return self.results
    
    def benchmark_speed(self, text_sizes=[10, 100, 1000]):
        """Benchmark correction speed for different text sizes"""
        if not self.corpus_handler:
            raise ValueError("Corpus handler is required for benchmarking")
            
        benchmark_results = {}
        words = list(self.corpus_handler.get_top_words(1000).keys())
        
        for size in text_sizes:
            # Generate text of specified size
            text_words = [random.choice(words) for _ in range(size)]
            text = ' '.join(text_words)
            
            # Measure correction time
            start_time = time.time()
            self.corrector.correct_text(text)
            elapsed_time = time.time() - start_time
            
            benchmark_results[size] = {
                'time': elapsed_time,
                'words_per_second': size / elapsed_time if elapsed_time > 0 else 0
            }
            
        return benchmark_results
    
    def get_confusion_matrix(self, test_data=None, size=100):
        """Generate a confusion matrix for the most common error patterns"""
        if not test_data:
            test_data = self._generate_test_data(size=size)
            
        error_patterns = Counter()
        
        for misspelled, original in test_data:
            if misspelled == original:
                continue
                
            prediction = self.corrector.correct_word(misspelled)
            
            if prediction != original:
                # Record the error pattern
                error_patterns[(original, prediction)] += 1
                
        return error_patterns
    
    def print_results(self):
        """Print evaluation results in a readable format"""
        if not self.results:
            print("No evaluation results available. Run evaluation first.")
            return
            
        print("=" * 50)
        print("SPELL CHECKER EVALUATION RESULTS")
        print("=" * 50)
        
        print(f"Word-Level Metrics:")
        print(f"  Accuracy:     {self.results.get('accuracy', 0):.4f}")
        print(f"  Precision:    {self.results.get('precision', 0):.4f}")
        print(f"  Recall:       {self.results.get('recall', 0):.4f}")
        print(f"  F1 Score:     {self.results.get('f1_score', 0):.4f}")
        
        if 'text_accuracy' in self.results:
            print(f"\nText-Level Metrics:")
            print(f"  Accuracy:     {self.results.get('text_accuracy', 0):.4f}")
        
        print(f"\nPerformance:")
        print(f"  Avg time/word: {self.results.get('avg_time_per_word', 0) * 1000:.2f} ms")
        
        if 'avg_time_per_text' in self.results:
            print(f"  Avg time/text: {self.results.get('avg_time_per_text', 0) * 1000:.2f} ms")
        
        print(f"\nTest Data:")
        print(f"  Total words:  {self.results.get('total_words', 0)}")
        print(f"  Correct predictions: {self.results.get('correct_predictions', 0)}")
        
        if 'num_texts' in self.results:
            print(f"  Number of texts: {self.results.get('num_texts', 0)}")
            
        print("=" * 50) 