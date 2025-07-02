import os
import sys
import argparse
from .corrector import Corrector
from .corpus import CorpusHandler
from .evaluation import SpellCheckerEvaluator

def create_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='Auto-Correct System using NLP techniques',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Correct text command
    correct_parser = subparsers.add_parser('correct', help='Correct text input')
    correct_parser.add_argument('-t', '--text', help='Text to correct')
    correct_parser.add_argument('-f', '--file', help='File containing text to correct')
    correct_parser.add_argument('-o', '--output', help='Output file for corrected text')
    correct_parser.add_argument('-d', '--dictionary', help='Custom dictionary file path')
    correct_parser.add_argument('-c', '--context', action='store_true', 
                                help='Use context-aware correction')
    
    # Evaluate command
    eval_parser = subparsers.add_parser('evaluate', help='Evaluate the auto-correction system')
    eval_parser.add_argument('-c', '--corpus', help='Corpus file for evaluation')
    eval_parser.add_argument('-s', '--size', type=int, default=100, 
                             help='Number of test samples')
    eval_parser.add_argument('-t', '--text-eval', action='store_true',
                             help='Evaluate on text level instead of word level')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train on custom corpus')
    train_parser.add_argument('-c', '--corpus', required=True, 
                              help='Corpus file to train on')
    train_parser.add_argument('-o', '--output', required=True,
                              help='Output path for the trained dictionary')
    
    # Interactive mode
    interactive_parser = subparsers.add_parser('interactive', 
                                              help='Start interactive correction mode')
    interactive_parser.add_argument('-d', '--dictionary', 
                                   help='Custom dictionary file path')
    
    return parser

def correct_text(args):
    """Correct text from input or file"""
    # Initialize corrector with custom dictionary if provided
    corrector = Corrector(custom_dict_path=args.dictionary)
    
    # Get text from argument or file
    if args.text:
        text = args.text
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return
    else:
        print("No text or file provided. Use --text or --file.")
        return
    
    # Correct the text
    if args.context:
        corrected_text = corrector.correct_with_context(text)
    else:
        corrected_text = corrector.correct_text(text)
    
    # Output the corrected text
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(corrected_text)
            print(f"Corrected text saved to {args.output}")
        except Exception as e:
            print(f"Error writing to output file: {e}")
    else:
        print("\nOriginal Text:")
        print("-" * 50)
        print(text)
        print("\nCorrected Text:")
        print("-" * 50)
        print(corrected_text)

def evaluate_system(args):
    """Evaluate the auto-correction system"""
    # Initialize corrector
    corrector = Corrector()
    
    # Initialize corpus handler
    corpus_handler = CorpusHandler(args.corpus)
    
    # Initialize evaluator
    evaluator = SpellCheckerEvaluator(corrector, corpus_handler)
    
    # Run evaluation
    if args.text_eval:
        print("Evaluating text-level correction...")
        evaluator.evaluate_text_correction(num_sentences=args.size // 10)
    else:
        print("Evaluating word-level correction...")
        evaluator.evaluate_word_correction(size=args.size)
    
    # Print results
    evaluator.print_results()
    
    # Also run speed benchmark
    print("\nRunning speed benchmark...")
    benchmark_results = evaluator.benchmark_speed()
    
    print("\nSpeed Benchmark Results:")
    print("-" * 50)
    for size, results in benchmark_results.items():
        print(f"Text size: {size} words")
        print(f"  Time: {results['time']:.4f} seconds")
        print(f"  Speed: {results['words_per_second']:.2f} words/second")

def train_system(args):
    """Train the system on a custom corpus"""
    try:
        # Initialize corpus handler with the provided corpus
        print(f"Loading corpus from {args.corpus}...")
        corpus_handler = CorpusHandler(args.corpus)
        
        # Export word frequencies
        print(f"Exporting word frequencies to {args.output}...")
        corpus_handler.export_word_frequencies(args.output)
        
        print("Training completed successfully.")
        
    except Exception as e:
        print(f"Error during training: {e}")

def interactive_mode(args):
    """Start interactive correction mode"""
    corrector = Corrector(custom_dict_path=args.dictionary)
    
    print("=" * 50)
    print("Auto-Correct Interactive Mode")
    print("=" * 50)
    print("Type your text for correction. Type 'q' or 'quit' to exit.")
    print("Type 'c <word> <correction>' to add a custom correction.")
    print("-" * 50)
    
    while True:
        try:
            user_input = input("\nEnter text: ").strip()
            
            if user_input.lower() in ['q', 'quit', 'exit']:
                break
                
            if user_input.startswith('c '):
                # Add custom correction
                parts = user_input.split(maxsplit=2)
                if len(parts) == 3:
                    _, wrong, right = parts
                    corrector.add_user_correction(wrong, right)
                    print(f"Added correction: '{wrong}' -> '{right}'")
                else:
                    print("Invalid format. Use: c <wrong_word> <right_word>")
            else:
                # Correct the text
                corrected = corrector.correct_with_context(user_input)
                print("\nCorrected: " + corrected)
                
                if corrected != user_input:
                    # Show differences
                    original_words = user_input.split()
                    corrected_words = corrected.split()
                    
                    min_len = min(len(original_words), len(corrected_words))
                    
                    print("\nChanges:")
                    has_changes = False
                    for i in range(min_len):
                        if original_words[i] != corrected_words[i]:
                            print(f"  '{original_words[i]}' -> '{corrected_words[i]}'")
                            has_changes = True
                            
                    if not has_changes:
                        print("  No word-level changes (punctuation or spacing only)")
        
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
    
    print("\nExiting interactive mode.")

def main():
    """Main entry point for the CLI"""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.command == 'correct':
        correct_text(args)
    elif args.command == 'evaluate':
        evaluate_system(args)
    elif args.command == 'train':
        train_system(args)
    elif args.command == 'interactive':
        interactive_mode(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 