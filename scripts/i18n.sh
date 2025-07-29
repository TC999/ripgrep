#!/bin/bash
#
# Quick i18n string extraction script for ripgrep
# 
# This script provides a simple interface to the Python extraction tool
# and includes common workflows for i18n management.
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/i18n_extract.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python script exists
if [[ ! -f "$PYTHON_SCRIPT" ]]; then
    echo -e "${RED}Error: Python extraction script not found at $PYTHON_SCRIPT${NC}"
    exit 1
fi

# Function to show usage
show_usage() {
    echo "ripgrep i18n String Extraction Tool"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  scan      - Scan codebase for translatable strings"
    echo "  extract   - Extract strings and add to .ftl files"
    echo "  update    - Update existing translations (scan + extract)"
    echo "  stats     - Show translation statistics"
    echo "  validate  - Validate existing translation files"
    echo "  interactive - Run interactive extraction mode"
    echo ""
    echo "Examples:"
    echo "  $0 scan                    # Find translatable strings"
    echo "  $0 extract                 # Add new strings to .ftl files"
    echo "  $0 update                  # Full update workflow"
    echo "  $0 interactive             # Interactive mode"
}

# Function to show stats
show_stats() {
    echo -e "${BLUE}📊 Translation Statistics${NC}"
    echo "========================="
    
    for lang_dir in "$REPO_ROOT"/i18n/*/; do
        if [[ -d "$lang_dir" ]]; then
            lang=$(basename "$lang_dir")
            ftl_file="$lang_dir/ripgrep.ftl"
            
            if [[ -f "$ftl_file" ]]; then
                total_lines=$(wc -l < "$ftl_file")
                translation_lines=0
                todo_lines=0
                
                # Count translation lines
                if grep -q "^[a-zA-Z_][a-zA-Z0-9_]* *=" "$ftl_file" 2>/dev/null; then
                    translation_lines=$(grep -c "^[a-zA-Z_][a-zA-Z0-9_]* *=" "$ftl_file" 2>/dev/null)
                fi
                
                # Count TODO lines
                if grep -q "TODO:" "$ftl_file" 2>/dev/null; then
                    todo_lines=$(grep -c "TODO:" "$ftl_file" 2>/dev/null)
                fi
                
                echo -e "${GREEN}$lang${NC}:"
                echo "  Total lines: $total_lines"
                echo "  Translations: $translation_lines"
                if [[ "$todo_lines" -gt 0 ]]; then
                    echo -e "  ${YELLOW}TODO items: $todo_lines${NC}"
                fi
                echo ""
            fi
        fi
    done
}

# Function to validate translation files
validate_translations() {
    echo -e "${BLUE}🔍 Validating Translation Files${NC}"
    echo "==============================="
    
    error_count=0
    
    for lang_dir in "$REPO_ROOT"/i18n/*/; do
        if [[ -d "$lang_dir" ]]; then
            lang=$(basename "$lang_dir")
            ftl_file="$lang_dir/ripgrep.ftl"
            
            if [[ -f "$ftl_file" ]]; then
                echo "Checking $lang..."
                
                # Check for duplicate keys
                duplicates=$(grep "^[a-zA-Z_][a-zA-Z0-9_]* *=" "$ftl_file" | cut -d'=' -f1 | sed 's/^[0-9]*\.//' | sort | uniq -d)
                if [[ -n "$duplicates" ]]; then
                    echo -e "  ${RED}❌ Duplicate keys found:${NC}"
                    echo "$duplicates" | sed 's/^/    /'
                    ((error_count++))
                fi
                
                # Check for missing translations (TODO items)
                todo_count=0
                if grep -q "TODO:" "$ftl_file" 2>/dev/null; then
                    todo_count=$(grep -c "TODO:" "$ftl_file" 2>/dev/null)
                fi
                if [[ "$todo_count" -gt 0 && "$lang" != "en-US" ]]; then
                    echo -e "  ${YELLOW}⚠️  $todo_count missing translations${NC}"
                fi
                
                echo -e "  ${GREEN}✅ Basic validation passed${NC}"
            else
                echo -e "  ${RED}❌ Translation file missing: $ftl_file${NC}"
                ((error_count++))
            fi
        fi
    done
    
    if [[ $error_count -eq 0 ]]; then
        echo -e "\n${GREEN}🎉 All translation files are valid!${NC}"
    else
        echo -e "\n${RED}❌ Found $error_count validation errors${NC}"
        exit 1
    fi
}

# Main script logic
case "${1:-interactive}" in
    "scan")
        echo -e "${BLUE}🔍 Scanning for translatable strings...${NC}"
        python3 "$PYTHON_SCRIPT" --scan --repo-root "$REPO_ROOT"
        ;;
    
    "extract")
        echo -e "${BLUE}📥 Extracting strings to .ftl files...${NC}"
        python3 "$PYTHON_SCRIPT" --extract --repo-root "$REPO_ROOT"
        echo -e "${GREEN}✅ Extraction complete!${NC}"
        echo -e "${YELLOW}💡 Don't forget to translate TODO items in non-English .ftl files${NC}"
        ;;
    
    "update")
        echo -e "${BLUE}🔄 Running full update workflow...${NC}"
        echo ""
        echo "Step 1: Scanning for new strings..."
        python3 "$PYTHON_SCRIPT" --scan --repo-root "$REPO_ROOT"
        echo ""
        echo "Step 2: Extracting to .ftl files..."
        python3 "$PYTHON_SCRIPT" --extract --repo-root "$REPO_ROOT"
        echo ""
        echo "Step 3: Showing updated stats..."
        show_stats
        echo -e "${GREEN}✅ Update complete!${NC}"
        ;;
    
    "stats")
        show_stats
        ;;
    
    "validate")
        validate_translations
        ;;
    
    "interactive")
        echo -e "${BLUE}🎯 Starting interactive mode...${NC}"
        python3 "$PYTHON_SCRIPT" --interactive --repo-root "$REPO_ROOT"
        ;;
    
    "help"|"-h"|"--help")
        show_usage
        ;;
    
    *)
        echo -e "${RED}Error: Unknown command '$1'${NC}"
        echo ""
        show_usage
        exit 1
        ;;
esac