#!/usr/bin/env python3
"""
i18n String Extraction and Automation Script for ripgrep

This script helps automate the process of marking strings for internationalization:
1. Scans Rust source files for potential translatable strings
2. Generates translation keys and adds them to .ftl files  
3. Optionally updates source code to use fl! macros
4. Supports interactive and batch modes

Usage:
  python3 scripts/i18n_extract.py --scan          # Scan for translatable strings
  python3 scripts/i18n_extract.py --extract       # Extract and add to .ftl files
  python3 scripts/i18n_extract.py --apply         # Apply fl! macro replacements
  python3 scripts/i18n_extract.py --interactive   # Interactive mode
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass

@dataclass
class TranslatableString:
    """Represents a string that can be translated"""
    text: str
    file_path: str
    line_number: int
    context: str
    suggested_key: str
    confidence: float

class I18nExtractor:
    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.i18n_dir = self.repo_root / "i18n"
        self.src_dirs = [
            self.repo_root / "crates" / "core",
            self.repo_root / "crates" / "grep",
            self.repo_root / "src"
        ]
        
        # Patterns for identifying translatable strings
        self.translatable_patterns = [
            # Error messages
            (r'anyhow::bail!\s*\(\s*"([^"]+)"\s*\)', 'error', 0.9),
            (r'eprintln!\s*\(\s*"([^"]+)"', 'error', 0.8),
            (r'return\s+Err\s*\([^"]*"([^"]+)"', 'error', 0.8),
            
            # User messages
            (r'println!\s*\(\s*"([^"]+)"', 'message', 0.7),
            (r'print!\s*\(\s*"([^"]+)"', 'message', 0.7),
            
            # Format strings with user content
            (r'format!\s*\(\s*"([^"]+)"', 'format', 0.6),
            
            # Direct string literals in user-facing contexts
            (r'"([A-Z][^"]{10,})"', 'literal', 0.5),
        ]
        
        # Exclude patterns (strings that shouldn't be translated)
        self.exclude_patterns = [
            r'^[a-z_]+$',  # Variable names
            r'^[A-Z_]+$',  # Constants
            r'^\w+::\w+',  # Rust paths
            r'^/[^"]*$',   # File paths
            r'^\d+$',      # Numbers only
            r'^[^a-zA-Z]*$',  # No letters
        ]
        
        self.existing_keys = self._load_existing_keys()
    
    def _load_existing_keys(self) -> Set[str]:
        """Load existing translation keys from .ftl files"""
        keys = set()
        for lang_dir in self.i18n_dir.glob("*/"):
            ftl_file = lang_dir / "ripgrep.ftl"
            if ftl_file.exists():
                with open(ftl_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#') and line:
                            key = line.split('=')[0].strip()
                            keys.add(key)
        return keys
    
    def _generate_key(self, text: str, context: str) -> str:
        """Generate a translation key from text and context"""
        # Clean the text
        clean_text = re.sub(r'[^a-zA-Z0-9\s]', '', text.lower())
        words = clean_text.split()[:4]  # Use first 4 words max
        
        # Create base key
        if context == 'error':
            prefix = 'error_'
        elif context == 'message':
            prefix = 'msg_'
        elif context == 'format':
            prefix = 'fmt_'
        else:
            prefix = ''
            
        key = prefix + '_'.join(words)
        
        # Ensure uniqueness
        counter = 1
        original_key = key
        while key in self.existing_keys:
            key = f"{original_key}_{counter}"
            counter += 1
            
        return key
    
    def _should_exclude(self, text: str) -> bool:
        """Check if a string should be excluded from translation"""
        for pattern in self.exclude_patterns:
            if re.match(pattern, text):
                return True
        return False
    
    def scan_file(self, file_path: Path) -> List[TranslatableString]:
        """Scan a single Rust file for translatable strings"""
        if not file_path.suffix == '.rs':
            return []
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return []
            
        results = []
        lines = content.split('\n')
        
        for pattern, context, confidence in self.translatable_patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                text = match.group(1)
                
                # Skip if should be excluded
                if self._should_exclude(text):
                    continue
                    
                # Find line number
                line_num = content[:match.start()].count('\n') + 1
                line_context = lines[line_num - 1].strip() if line_num <= len(lines) else ""
                
                # Generate suggested key
                suggested_key = self._generate_key(text, context)
                
                results.append(TranslatableString(
                    text=text,
                    file_path=str(file_path.relative_to(self.repo_root)),
                    line_number=line_num,
                    context=line_context,
                    suggested_key=suggested_key,
                    confidence=confidence
                ))
        
        return results
    
    def scan_codebase(self) -> List[TranslatableString]:
        """Scan the entire codebase for translatable strings"""
        all_strings = []
        
        for src_dir in self.src_dirs:
            if not src_dir.exists():
                continue
                
            for rs_file in src_dir.rglob("*.rs"):
                strings = self.scan_file(rs_file)
                all_strings.extend(strings)
        
        # Sort by confidence and remove duplicates
        seen_texts = set()
        unique_strings = []
        
        for s in sorted(all_strings, key=lambda x: x.confidence, reverse=True):
            if s.text not in seen_texts:
                seen_texts.add(s.text)
                unique_strings.append(s)
        
        return unique_strings
    
    def add_to_ftl_files(self, strings: List[TranslatableString]):
        """Add translation keys to .ftl files"""
        # Group strings by suggested key
        key_map = {}
        for s in strings:
            if s.suggested_key not in key_map:
                key_map[s.suggested_key] = s
        
        # Add to all language files
        for lang_dir in self.i18n_dir.glob("*/"):
            ftl_file = lang_dir / "ripgrep.ftl"
            if not ftl_file.exists():
                continue
                
            # Read existing content
            with open(ftl_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Add new entries
            new_lines = []
            for key, string_obj in key_map.items():
                if key not in self.existing_keys:
                    if lang_dir.name == 'en-US':
                        # Use original text for English
                        new_lines.append(f"{key} = {string_obj.text}\n")
                    else:
                        # Use placeholder for other languages
                        new_lines.append(f"{key} = TODO: {string_obj.text}\n")
            
            if new_lines:
                # Append new translations
                with open(ftl_file, 'a', encoding='utf-8') as f:
                    f.write('\n# Auto-generated translations\n')
                    f.writelines(new_lines)
                
                print(f"Added {len(new_lines)} new translations to {ftl_file}")
    
    def generate_replacements(self, strings: List[TranslatableString]) -> Dict[str, str]:
        """Generate fl! macro replacements for source code"""
        replacements = {}
        
        for s in strings:
            original = f'"{s.text}"'
            replacement = f'fl!(crate::i18n::LANGUAGE_LOADER, "{s.suggested_key}")'
            
            file_path = self.repo_root / s.file_path
            if file_path not in replacements:
                replacements[str(file_path)] = []
            
            replacements[str(file_path)].append({
                'line': s.line_number,
                'original': original,
                'replacement': replacement,
                'context': s.context
            })
        
        return replacements
    
    def interactive_mode(self):
        """Run interactive mode for reviewing and applying translations"""
        print("🌍 ripgrep i18n String Extraction Tool")
        print("=" * 50)
        
        strings = self.scan_codebase()
        print(f"Found {len(strings)} potential translatable strings")
        
        if not strings:
            print("No translatable strings found!")
            return
        
        # Show top candidates
        print("\nTop candidates (by confidence):")
        for i, s in enumerate(strings[:10]):
            print(f"{i+1:2}. [{s.confidence:.1f}] {s.suggested_key}")
            print(f"    Text: '{s.text}'")
            print(f"    File: {s.file_path}:{s.line_number}")
            print(f"    Context: {s.context[:60]}...")
            print()
        
        # Ask user what to do
        while True:
            choice = input("Choose action: (a)dd to .ftl files, (g)enerate replacements, (q)uit: ").lower()
            
            if choice == 'q':
                break
            elif choice == 'a':
                self.add_to_ftl_files(strings)
                print("✅ Added translations to .ftl files")
            elif choice == 'g':
                replacements = self.generate_replacements(strings)
                
                # Save replacements to file
                replacements_file = self.repo_root / "i18n_replacements.json"
                with open(replacements_file, 'w') as f:
                    json.dump(replacements, f, indent=2)
                
                print(f"✅ Generated replacements saved to {replacements_file}")
                print("Review the file and apply manually, or use --apply flag")
            else:
                print("Invalid choice")

def main():
    parser = argparse.ArgumentParser(description="ripgrep i18n automation tool")
    parser.add_argument("--scan", action="store_true", help="Scan for translatable strings")
    parser.add_argument("--extract", action="store_true", help="Extract strings to .ftl files")
    parser.add_argument("--apply", action="store_true", help="Apply fl! macro replacements")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--repo-root", default=".", help="Repository root directory")
    
    args = parser.parse_args()
    
    extractor = I18nExtractor(args.repo_root)
    
    if args.interactive or not any([args.scan, args.extract, args.apply]):
        extractor.interactive_mode()
    else:
        strings = extractor.scan_codebase()
        
        if args.scan:
            print(f"Found {len(strings)} translatable strings:")
            for s in strings:
                print(f"  {s.file_path}:{s.line_number} - {s.text}")
        
        if args.extract:
            extractor.add_to_ftl_files(strings)
        
        if args.apply:
            replacements = extractor.generate_replacements(strings)
            print("Generated replacements - review i18n_replacements.json and apply manually")

if __name__ == "__main__":
    main()