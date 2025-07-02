from simple_corrector import SimpleCorrector

def print_colored(text, color):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'end': '\033[0m'
    }
    print(f"{colors.get(color, '')}{text}{colors['end']}")

def main():
    corrector = SimpleCorrector()
    
    print_colored("\n=== Simple Auto-Correct System ===", 'blue')
    print_colored("Type your text and press Enter to see corrections.", 'yellow')
    print_colored("Type 'quit' to exit.\n", 'yellow')
    
    while True:
        try:
            # Get input from user
            text = input("\nEnter text: ").strip()
            
            # Check for quit command
            if text.lower() == 'quit':
                print_colored("\nGoodbye!", 'green')
                break
            
            # Skip empty input
            if not text:
                continue
            
            # Get correction
            corrected = corrector.correct_text(text)
            
            # Show results
            if corrected.lower() != text.lower():
                print_colored("\nOriginal text:", 'yellow')
                print(text)
                print_colored("\nCorrected text:", 'green')
                print(corrected)
                
                # Show changes
                original_words = text.split()
                corrected_words = corrected.split()
                min_len = min(len(original_words), len(corrected_words))
                
                changes = []
                for i in range(min_len):
                    if original_words[i].lower() != corrected_words[i].lower():
                        changes.append(f"'{original_words[i]}' → '{corrected_words[i]}'")
                
                if changes:
                    print_colored("\nChanges made:", 'blue')
                    print(", ".join(changes))
            else:
                print_colored("\nNo corrections needed! ✨", 'green')
                
        except KeyboardInterrupt:
            print_colored("\n\nGoodbye!", 'green')
            break
        except Exception as e:
            print_colored(f"\nError: {str(e)}", 'red')

if __name__ == '__main__':
    main() 