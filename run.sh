#!/usr/bin/env bash

# Active Inference Matrix Runner
# The most ridiculously over-engineered terminal script in the multiverse
# "Welcome to the Active Inference Matrix, Neo..." 🕶️

set -euo pipefail

# Color and animation constants
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
MAGENTA='\033[35m'
CYAN='\033[36m'
WHITE='\033[37m'
MATRIX_GREEN='\033[38;2;0;255;65m'
CYBER_BLUE='\033[38;2;0;255;255m'
GOLD='\033[38;2;255;215;0m'
RESET='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

# ASCII Art Banner (because we're fancy like that)
MATRIX_BANNER="
${MATRIX_GREEN}╔═══════════════════════════════════════════════════════════════╗
║  █████╗  ██████╗████████╗██╗██╗   ██╗███████╗                ║
║ ██╔══██╗██╔════╝╚══██╔══╝██║██║   ██║██╔════╝                ║
║ ███████║██║        ██║   ██║██║   ██║█████╗                  ║
║ ██╔══██║██║        ██║   ██║╚██╗ ██╔╝██╔══╝                  ║
║ ██║  ██║╚██████╗   ██║   ██║ ╚████╔╝ ███████╗                ║
║ ╚═╝  ╚═╝ ╚═════╝   ╚═╝   ╚═╝  ╚═══╝  ╚══════╝                ║
║                                                               ║
║ ██╗███╗   ██╗███████╗███████╗██████╗ ███████╗███╗   ██╗ ██████╗║
║ ██║████╗  ██║██╔════╝██╔════╝██╔══██╗██╔════╝████╗  ██║██╔════╝║
║ ██║██╔██╗ ██║█████╗  █████╗  ██████╔╝█████╗  ██╔██╗ ██║██║     ║
║ ██║██║╚██╗██║██╔══╝  ██╔══╝  ██╔══██╗██╔══╝  ██║╚██╗██║██║     ║
║ ██║██║ ╚████║██║     ███████╗██║  ██║███████╗██║ ╚████║╚██████╗║
║ ╚═╝╚═╝  ╚═══╝╚═╝     ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝ ╚═════╝║
║                                                               ║
║              ${CYBER_BLUE}🤖 THE MATRIX RUNNER 🤖${MATRIX_GREEN}                    ║
║         ${DIM}Where AI meets overly dramatic terminal UI${MATRIX_GREEN}         ║
╚═══════════════════════════════════════════════════════════════╝${RESET}
"

# Get terminal dimensions for proper centering
TERMINAL_WIDTH=$(tput cols 2>/dev/null || echo 80)
TERMINAL_HEIGHT=$(tput lines 2>/dev/null || echo 24)

# Function to center text
center_text() {
    local text="$1"
    local width=${2:-$TERMINAL_WIDTH}
    local padding=$(( (width - ${#text}) / 2 ))
    printf "%*s%s\n" $padding "" "$text"
}

# Matrix-style loading animation
matrix_loading() {
    local message="$1"
    local duration=${2:-2}
    
    echo -e "${MATRIX_GREEN}"
    
    # Hide cursor
    tput civis
    
    # Matrix rain effect (simplified)
    for ((i=0; i<duration*10; i++)); do
        # Clear screen
        clear
        
        # Show message
        echo -e "\n\n"
        center_text "$message"
        echo -e "\n"
        
        # Generate random matrix characters
        for ((j=0; j<5; j++)); do
            line=""
            for ((k=0; k<$TERMINAL_WIDTH; k++)); do
                if [ $((RANDOM % 10)) -eq 0 ]; then
                    chars="0123456789ABCDEF!@#$%^&*()_+-="
                    char=${chars:$((RANDOM % ${#chars})):1}
                    line+="$char"
                else
                    line+=" "
                fi
            done
            echo -e "${DIM}$line${RESET}${MATRIX_GREEN}"
        done
        
        sleep 0.1
    done
    
    # Show cursor
    tput cnorm
    echo -e "${RESET}"
}

# Dramatic typewriter effect
typewriter() {
    local text="$1"
    local delay=${2:-0.05}
    local color=${3:-$MATRIX_GREEN}
    
    echo -en "$color"
    for ((i=0; i<${#text}; i++)); do
        echo -n "${text:$i:1}"
        sleep "$delay"
    done
    echo -e "${RESET}"
}

# Glitch effect
glitch_text() {
    local text="$1"
    local iterations=${2:-5}
    local color=${3:-$RED}
    
    local glitch_chars="!@#$%^&*()_+-=[]{}|;:,.<>?~\`"
    
    for ((i=0; i<iterations; i++)); do
        local glitched=""
        for ((j=0; j<${#text}; j++)); do
            if [ $((RANDOM % 4)) -eq 0 ]; then
                local rand_char=${glitch_chars:$((RANDOM % ${#glitch_chars})):1}
                glitched+="$rand_char"
            else
                glitched+="${text:$j:1}"
            fi
        done
        
        echo -en "\r${color}${BOLD}$glitched${RESET}"
        sleep 0.1
    done
    
    echo -en "\r${MATRIX_GREEN}$text${RESET}"
    sleep 0.2
    echo
}

# Spinning loader
spinner_load() {
    local message="$1"
    local duration=${2:-3}
    
    local spinner='/-\|'
    local i=0
    
    tput civis
    
    for ((count=0; count<duration*10; count++)); do
        i=$(( (i+1) %4 ))
        printf "\r${MATRIX_GREEN}${spinner:$i:1} ${message}${RESET}"
        sleep 0.1
    done
    
    printf "\r${GREEN}✅ ${message} - COMPLETE${RESET}\n"
    tput cnorm
}

# Boot sequence animation
boot_sequence() {
    clear
    
    echo -e "${CYBER_BLUE}${BOLD}"
    echo "INITIALIZING ACTIVE INFERENCE MATRIX..."
    echo -e "${RESET}"
    
    local steps=(
        "Loading quantum consciousness modules"
        "Calibrating Free Energy Principle engines"
        "Downloading the universe (this may take a while)"
        "Pre-compiling philosophical implications"
        "Syncing with the Bayesian multiverse"
        "Initializing Open Source Intelligence"
        "Entering the Active Inference Institute ~ ∞"
    )
    
    for step in "${steps[@]}"; do
        spinner_load "$step" 1
        sleep 0.2
    done
    
    echo -e "\n${GOLD}${BOLD}🎭 DRAMATIC LOADING COMPLETE 🎭${RESET}"
    sleep 1
}

# System health check with dramatic flair
system_health_check() {
    clear
    echo "$MATRIX_BANNER"
    
    typewriter "🔍 INITIATING COMPREHENSIVE SYSTEM DIAGNOSTICS..." 0.03
    echo
    
    # Check if we're in the right directory
    if [[ ! -f "pyproject.toml" ]]; then
        glitch_text "ERROR: NOT IN PROJECT ROOT DIRECTORY" 3 "$RED"
        echo -e "${RED}Please run this script from the project root directory.${RESET}"
        exit 1
    fi
    
    typewriter "📊 Running Python-based system analysis..." 0.03
    echo
    
    # Run our comprehensive system reporting
    if command -v uv >/dev/null 2>&1; then
        uv run python -c "
from src.system.reporting import generate_system_report, format_system_report
from src.system.dependencies import run_comprehensive_dependency_check, format_dependency_report
from src.terminal.colors import matrix_text

print(matrix_text('=' * 60, 'bright'))
print(matrix_text('🖥️  SYSTEM DIAGNOSTIC REPORT', 'gold'))
print(matrix_text('=' * 60, 'bright'))

# System info
system_info = generate_system_report()
print(format_system_report(system_info, detailed=False))

print()
print(matrix_text('=' * 60, 'bright'))
print(matrix_text('📦 DEPENDENCY CHECK REPORT', 'gold'))  
print(matrix_text('=' * 60, 'bright'))

# Dependencies
dep_report = run_comprehensive_dependency_check()
print(format_dependency_report(dep_report, show_optional=False))

if not dep_report.all_required_available:
    print()
    print(matrix_text('⚠️  MISSING REQUIRED DEPENDENCIES', 'warning'))
    print(matrix_text('Run the Environment Setup option to fix issues.', 'dim'))
"
    else
        echo -e "${YELLOW}⚠️  uv not found - install with: curl -LsSf https://astral.sh/uv/install.sh | sh${RESET}"
        echo -e "${YELLOW}📱 Basic system information:${RESET}"
        echo "OS: $(uname -s) $(uname -r)"
        echo "Architecture: $(uname -m)"
        echo "Python: $(python3 --version 2>/dev/null || echo 'Not found')"
        echo "Git: $(git --version 2>/dev/null || echo 'Not found')"
    fi
    
    echo
    typewriter "📋 System diagnostic complete!" 0.05 "$GREEN"
}

# Repository management with style
repo_management() {
    clear
    echo "$MATRIX_BANNER"
    
    typewriter "📚 ACCESSING THE REPOSITORY MATRIX..." 0.03
    echo
    
    if ! command -v uv >/dev/null 2>&1; then
        echo -e "${RED}❌ uv not found. Please install uv first.${RESET}"
        read -p "Press Enter to continue..."
        return
    fi
    
    # Show repository menu
    uv run python -c "
from src.repos.manager import create_repository_manager, format_repository_summary
from src.terminal.menu import MenuBuilder, confirmation_dialog, input_dialog
from src.terminal.colors import matrix_text
from src.terminal.animations import print_animated, matrix_banner

manager = create_repository_manager()

def show_repo_summary():
    summary = manager.get_summary()
    print(matrix_banner('REPOSITORY SUMMARY'))
    print(format_repository_summary(summary))
    input(matrix_text('\nPress Enter to continue...', 'dim'))

def clone_single_repo():
    available = manager.list_available_repositories()
    print(matrix_banner('AVAILABLE REPOSITORIES'))
    for name, info in available.items():
        print(f'{matrix_text(name, \"bright\")}: {info[\"description\"]}')
    
    repo_name = input_dialog('Enter repository name to clone:')
    if repo_name and repo_name in available:
        if confirmation_dialog(f'Clone {repo_name}?', True):
            print_animated('Cloning repository...', 'typewriter')
            result = manager.clone_repository(repo_name, progress_callback=print)
            if result.success:
                print(matrix_text(f'✅ Successfully cloned {repo_name}', 'bright'))
            else:
                print(matrix_text(f'❌ Failed to clone {repo_name}: {result.error_message}', 'warning'))
    elif repo_name:
        print(matrix_text(f'Unknown repository: {repo_name}', 'warning'))
    input(matrix_text('Press Enter to continue...', 'dim'))

def clone_all_repos():
    if confirmation_dialog('Clone ALL repositories? This may take several minutes.', False):
        print_animated('Cloning all repositories...', 'typewriter')
        results = manager.clone_all(progress_callback=print)
        successful = sum(1 for r in results if r.success)
        print(matrix_text(f'Completed: {successful}/{len(results)} successful', 'bright'))
    input(matrix_text('Press Enter to continue...', 'dim'))

def show_cloned_repos():
    from src.repos.manager import format_repository_status
    cloned = manager.list_cloned_repositories()
    if cloned:
        print(matrix_banner('CLONED REPOSITORIES'))
        print(format_repository_status(cloned))
    else:
        print(matrix_text('No repositories cloned yet.', 'dim'))
    input(matrix_text('Press Enter to continue...', 'dim'))

# Build repository menu
menu = (MenuBuilder('REPOSITORY MATRIX')
    .add_item('📊 Show Repository Summary', show_repo_summary, 'View summary of available and cloned repositories')
    .add_item('📥 Clone Single Repository', clone_single_repo, 'Clone a specific repository')
    .add_item('📦 Clone All Repositories', clone_all_repos, 'Clone all available repositories')
    .add_item('📋 Show Cloned Repositories', show_cloned_repos, 'View status of cloned repositories')
    .add_separator()
    .add_item('🔙 Return to Main Menu', lambda: None, 'Return to main menu')
    .build())

menu.show()
"
}

# Environment setup with maximum drama
environment_setup() {
    clear
    echo "$MATRIX_BANNER"
    
    glitch_text "INITIATING ENVIRONMENT RECONSTRUCTION PROTOCOL" 3
    echo
    
    typewriter "🔧 This will set up your complete development environment..." 0.03
    echo
    
    # Check if user wants to proceed
    echo -e "${CYAN}This will:${RESET}"
    echo -e "  ${GREEN}•${RESET} Install uv package manager (if needed)"
    echo -e "  ${GREEN}•${RESET} Set up Python virtual environment"
    echo -e "  ${GREEN}•${RESET} Install all required dependencies"
    echo -e "  ${GREEN}•${RESET} Create configuration templates"
    echo -e "  ${GREEN}•${RESET} Run comprehensive system validation"
    echo
    
    read -p "$(echo -e "${GOLD}Proceed with environment setup? [y/N]: ${RESET}")" -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Setup cancelled.${RESET}"
        return
    fi
    
    matrix_loading "RECONSTRUCTING REALITY" 2
    
    if command -v uv >/dev/null 2>&1; then
        echo -e "${GREEN}✅ uv package manager found${RESET}"
    else
        typewriter "Installing uv package manager..." 0.03
        if curl -LsSf https://astral.sh/uv/install.sh | sh; then
            echo -e "${GREEN}✅ uv installed successfully${RESET}"
            # Add to current PATH
            export PATH="$HOME/.cargo/bin:$PATH"
        else
            echo -e "${RED}❌ Failed to install uv${RESET}"
            return 1
        fi
    fi
    
    typewriter "Syncing project dependencies..." 0.03
    if uv sync --all-extras --dev; then
        echo -e "${GREEN}✅ Dependencies synced successfully${RESET}"
    else
        echo -e "${RED}❌ Failed to sync dependencies${RESET}"
        return 1
    fi
    
    # Run Python-based environment setup
    typewriter "Running comprehensive environment setup..." 0.03
    uv run python -c "
from src.system.environment import setup_project_environment, fix_common_issues
from src.terminal.colors import matrix_text
from src.terminal.animations import print_animated

print_animated('🔧 Setting up project environment...', 'typewriter')

success, messages = setup_project_environment()

for message in messages:
    print(message)

if not success:
    print()
    print(matrix_text('⚠️  Some issues were found. Attempting automatic fixes...', 'warning'))
    fixed = fix_common_issues()
    for fix in fixed:
        print(fix)

print()
if success:
    print(matrix_text('🎉 ENVIRONMENT SETUP COMPLETE!', 'gold'))
else:
    print(matrix_text('⚠️  Setup completed with some issues. Check .env file for API keys.', 'warning'))
"
    
    echo
    typewriter "🎭 Environment reconstruction complete!" 0.05 "$GOLD"
    echo -e "${DIM}(That was unnecessarily dramatic, but fun!)${RESET}"
    echo
    read -p "Press Enter to continue..." -r
}

# Curriculum generation with maximum pizzazz
run_curriculum_generator() {
    clear
    echo "$MATRIX_BANNER"
    
    typewriter "🧠 ACCESSING THE ACTIVE INFERENCE CURRICULUM MATRIX..." 0.03
    echo
    
    if ! command -v uv >/dev/null 2>&1; then
        echo -e "${RED}❌ uv not found. Please run Environment Setup first.${RESET}"
        read -p "Press Enter to continue..."
        return
    fi
    
    glitch_text "INITIALIZING EPISTEMIC & PRAGMATIC ASPECTS OF CONSCIOUSNESS" 5 "$CYBER_BLUE"
    echo
    
    typewriter "Preparing to generate mind-bending AI curricula..." 0.03
    typewriter "Warning: May cause existential questioning and sudden understanding of Bayesian brains..." 0.03 "$YELLOW"
    echo
    
    matrix_loading "CONNECTING TO THE FREE ENERGY PRINCIPLE" 3
    
    echo -e "${GOLD}${BOLD}🚀 Launching Interactive Curriculum Generator...${RESET}"
    echo
    
    # Run the actual curriculum generator in interactive mode
    uv run python learning/curriculum_creation/generate_custom_curriculum.py --interactive
    
    echo
    typewriter "🎓 Curriculum generation session complete!" 0.05 "$GREEN"
    read -p "Press Enter to continue..." -r
}

# Exit with style
dramatic_exit() {
    clear
    
    echo -e "${MATRIX_GREEN}"
    typewriter "Disconnecting from the Active Inference Matrix..." 0.05
    echo
    
    typewriter "Remember: There is no spoon... but there is definitely a Free Energy Principle." 0.03 "$CYAN"
    echo
    
    glitch_text "REALITY.EXE HAS STOPPED RESPONDING" 3 "$RED"
    
    echo -e "${DIM}"
    echo "Until next time, brave explorer of artificial consciousness..."
    echo "May your priors be informative and your posteriors be well-calibrated! 🧠✨"
    echo -e "${RESET}"
    
    # Matrix rain exit effect
    matrix_loading "DISCONNECTING" 1
    
    echo -e "${GREEN}Goodbye! 👋${RESET}"
    exit 0
}

# Main menu system
show_main_menu() {
    clear
    echo "$MATRIX_BANNER"
    
    typewriter "You've entered the Active Inference Matrix..." 0.03
    typewriter "Where Learning Systems meet over-engineered terminal art 🧠✨" 0.03 "$YELLOW"
    echo
    
    echo -e "${MATRIX_GREEN}${BOLD}Choose your digital destiny:${RESET}"
    echo
    echo -e "  ${GOLD}1.${RESET} 🔍 ${GREEN}System Health Check${RESET} - Diagnostic reports with unnecessary drama"
    echo -e "  ${GOLD}2.${RESET} 🔧 ${BLUE}Environment Setup${RESET} - Reconstruct reality (install dependencies)"
    echo -e "  ${GOLD}3.${RESET} 🧠 ${MAGENTA}Generate Curricula${RESET} - Create AI learning materials (the fun part!)"
    echo -e "  ${GOLD}4.${RESET} 📚 ${CYAN}Repository Manager${RESET} - Clone the Matrix (research repositories)"
    echo -e "  ${GOLD}5.${RESET} 🎭 ${RED}Exit Matrix${RESET} - Return to boring reality"
    echo
    
    read -p "$(echo -e "${MATRIX_GREEN}${BOLD}Enter your choice [1-5]: ${RESET}")" -r choice
    
    case "$choice" in
        1) system_health_check ;;
        2) environment_setup ;;
        3) run_curriculum_generator ;;
        4) repo_management ;;
        5) dramatic_exit ;;
        *)
            glitch_text "INVALID INPUT DETECTED" 3 "$RED"
            typewriter "Please choose a number between 1-5..." 0.05 "$YELLOW"
            sleep 1
            ;;
    esac
}

# Check for required commands
check_dependencies() {
    local missing=()
    
    command -v python3 >/dev/null 2>&1 || missing+=("python3")
    command -v git >/dev/null 2>&1 || missing+=("git")
    command -v curl >/dev/null 2>&1 || missing+=("curl")
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        echo -e "${RED}❌ Missing required commands: ${missing[*]}${RESET}"
        echo -e "${YELLOW}Please install the missing commands and try again.${RESET}"
        exit 1
    fi
}

# Ensure we're in the right directory
ensure_project_root() {
    if [[ ! -f "pyproject.toml" ]] || [[ ! -d "src" ]]; then
        echo -e "${RED}❌ This script must be run from the project root directory.${RESET}"
        echo -e "${YELLOW}Please cd to the directory containing pyproject.toml and try again.${RESET}"
        exit 1
    fi
}

# Main execution flow
main() {
    # Trap Ctrl+C for dramatic exit
    trap dramatic_exit SIGINT
    
    # Initial setup checks
    check_dependencies
    ensure_project_root
    
    # Welcome sequence
    boot_sequence
    
    # Main program loop
    while true; do
        show_main_menu
        echo
        read -p "$(echo -e "${DIM}Press Enter to continue...${RESET}")" -r
    done
}

# Welcome to the Matrix (always on!)
clear
echo -e "${MATRIX_GREEN}"
echo "Wake up, Neo... The Active Inference Matrix has you..."
echo "There is no spoon, but there is definitely a Free Energy Principle."
echo -e "${RESET}"
typewriter "Welcome to the most dramatically over-engineered AI curriculum system in existence..." 0.05 "$CYBER_BLUE"
echo

# Run the main program
main
