# i18n Automation Tools

This directory contains scripts to automate the internationalization (i18n) workflow for ripgrep.

## Scripts

### `i18n.sh` - Main i18n workflow script
A user-friendly shell script that provides common i18n operations:

```bash
# Quick workflows
./scripts/i18n.sh scan          # Find translatable strings
./scripts/i18n.sh extract       # Add new strings to .ftl files  
./scripts/i18n.sh update        # Full workflow (scan + extract + stats)
./scripts/i18n.sh stats         # Show translation statistics
./scripts/i18n.sh validate      # Validate translation files
./scripts/i18n.sh interactive   # Interactive mode
```

### `i18n_extract.py` - Advanced extraction engine
The underlying Python script that handles the heavy lifting:

```bash
# Direct usage
python3 scripts/i18n_extract.py --scan          # Scan only
python3 scripts/i18n_extract.py --extract       # Extract to .ftl files
python3 scripts/i18n_extract.py --interactive   # Interactive mode
```

## Workflow

### 1. Find New Translatable Strings
```bash
./scripts/i18n.sh scan
```
This scans the codebase for hardcoded strings that should be translated.

### 2. Add to Translation Files
```bash
./scripts/i18n.sh extract
```
This automatically adds discovered strings to all `.ftl` files:
- Adds original text to `en-US/ripgrep.ftl`
- Adds TODO placeholders to other language files

### 3. Translate TODO Items
Edit the non-English `.ftl` files to replace `TODO:` items with actual translations:

```fluent
# Before (auto-generated)
42.error_invalid_pattern = TODO: invalid pattern provided

# After (manually translated)  
42.error_invalid_pattern = 提供的模式无效
```

### 4. Apply fl! Macro in Code
Use the generated suggestions to update source code:

```rust
// Before
anyhow::bail!("invalid pattern provided")

// After  
anyhow::bail!(fl!(crate::i18n::LANGUAGE_LOADER, "error_invalid_pattern"))
```

## Features

### Smart String Detection
The scripts automatically detect translatable strings by looking for:
- Error messages (`anyhow::bail!`, `eprintln!`)
- User messages (`println!`, `print!`)
- Format strings (`format!`)
- String literals in user-facing contexts

### Intelligent Key Generation
Translation keys are automatically generated based on:
- String content (first few words)
- Context (error, message, format)
- Uniqueness (numbered suffixes if needed)

### Multi-language Support
All operations work across all supported languages:
- `en-US` (English) - gets original text
- `zh-CN` (Chinese) - gets TODO placeholders  
- `ja-JP` (Japanese) - gets TODO placeholders

### Validation
Built-in validation checks for:
- Duplicate translation keys
- Missing translation files
- TODO items needing translation

## Examples

### Full Update Workflow
```bash
# 1. Scan and extract new strings
./scripts/i18n.sh update

# 2. Translate TODO items in i18n/zh-CN/ripgrep.ftl and i18n/ja-JP/ripgrep.ftl

# 3. Update source code to use fl! macros

# 4. Validate everything works
./scripts/i18n.sh validate
```

### Interactive Mode
```bash
./scripts/i18n.sh interactive
```
This provides a guided workflow with:
- Top translation candidates
- Confidence scoring
- Interactive choices for next steps

### Check Translation Status
```bash
./scripts/i18n.sh stats
```
Shows statistics for each language including TODO counts.

## Integration with Development

### Pre-commit Hook
Add to `.git/hooks/pre-commit`:
```bash
#!/bin/bash
./scripts/i18n.sh validate
```

### CI/CD Integration  
Add to your CI pipeline:
```yaml
- name: Validate i18n
  run: ./scripts/i18n.sh validate
```

## Extending

### Adding New Languages
1. Create `i18n/[lang-code]/ripgrep.ftl`
2. Run `./scripts/i18n.sh extract` to populate with TODO items
3. Translate the TODO items

### Customizing Detection
Edit `i18n_extract.py` to modify:
- `translatable_patterns` - what strings to detect
- `exclude_patterns` - what strings to ignore
- `_generate_key()` - how translation keys are generated

This automation significantly reduces the manual work involved in maintaining ripgrep's internationalization!