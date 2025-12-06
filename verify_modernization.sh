#!/bin/bash
# Verification script for AIForTrading_Udacity modernization

echo "========================================"
echo "AIForTrading_Udacity Modernization Check"
echo "========================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

checks_passed=0
checks_total=0

check() {
    checks_total=$((checks_total + 1))
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
        checks_passed=$((checks_passed + 1))
    else
        echo -e "${RED}✗${NC} $2"
    fi
}

# Check 1: Python version
echo "1. Checking Python version..."
python3 --version | grep -q "3\.\(1[0-9]\|[2-9][0-9]\)" 
check $? "Python 3.10+ detected"

# Check 2: Required files exist
echo ""
echo "2. Checking required files..."
[ -f "README.md" ]; check $? "README.md exists"
[ -f "CHANGELOG.md" ]; check $? "CHANGELOG.md exists"
[ -f "QUICKSTART.md" ]; check $? "QUICKSTART.md exists"
[ -f "MODERNIZATION_SUMMARY.md" ]; check $? "MODERNIZATION_SUMMARY.md exists"
[ -f "requirements.txt" ]; check $? "requirements.txt exists"

# Check 3: Project files exist
echo ""
echo "3. Checking project files..."
[ -f "ProjectMomentum/home/TradingWithMomentum.ipynb" ]; check $? "Original notebook preserved"
[ -f "ProjectMomentum/home/TradingWithMomentum_Modernized.ipynb" ]; check $? "Modernized notebook exists"
[ -f "ProjectMomentum/home/helper.py" ]; check $? "helper.py exists"
[ -f "ProjectMomentum/home/project_helper.py" ]; check $? "project_helper.py exists"
[ -f "ProjectMomentum/home/project_tests.py" ]; check $? "project_tests.py exists"
[ -f "ProjectMomentum/home/requirements.txt" ]; check $? "Project requirements.txt exists"

# Check 4: Python modules compile
echo ""
echo "4. Checking Python module syntax..."
cd ProjectMomentum/home
python3 -m py_compile helper.py 2>/dev/null
check $? "helper.py compiles"
python3 -m py_compile project_helper.py 2>/dev/null
check $? "project_helper.py compiles"
python3 -m py_compile project_tests.py 2>/dev/null
check $? "project_tests.py compiles"
cd ../..

# Check 5: Notebook structure
echo ""
echo "5. Checking notebook structure..."
python3 -c "import json; nb=json.load(open('ProjectMomentum/home/TradingWithMomentum_Modernized.ipynb')); exit(0 if len(nb['cells']) >= 60 else 1)" 2>/dev/null
check $? "Modernized notebook has sufficient cells (60+)"

python3 -c "import json; nb=json.load(open('ProjectMomentum/home/TradingWithMomentum_Modernized.ipynb')); exit(0 if nb['metadata']['language_info']['version'].startswith('3.10') else 1)" 2>/dev/null
check $? "Notebook targets Python 3.10+"

# Check 6: Key functions exist in helper.py
echo ""
echo "6. Checking helper.py functions..."
grep -q "def calculate_sharpe_ratio" ProjectMomentum/home/helper.py
check $? "calculate_sharpe_ratio function exists"
grep -q "def calculate_max_drawdown" ProjectMomentum/home/helper.py
check $? "calculate_max_drawdown function exists"
grep -q "def calculate_fama_french_factors" ProjectMomentum/home/helper.py
check $? "calculate_fama_french_factors function exists"
grep -q "def dynamic_position_sizing" ProjectMomentum/home/helper.py
check $? "dynamic_position_sizing function exists"
grep -q "def apply_transaction_costs" ProjectMomentum/home/helper.py
check $? "apply_transaction_costs function exists"

# Check 7: Key functions exist in project_helper.py
echo ""
echo "7. Checking project_helper.py functions..."
grep -q "def plot_drawdown" ProjectMomentum/home/project_helper.py
check $? "plot_drawdown function exists"
grep -q "def plot_rolling_metrics" ProjectMomentum/home/project_helper.py
check $? "plot_rolling_metrics function exists"
grep -q "def plot_feature_importance" ProjectMomentum/home/project_helper.py
check $? "plot_feature_importance function exists"

# Check 8: Dependencies in requirements.txt
echo ""
echo "8. Checking requirements.txt content..."
grep -q "pandas>=2.0.0" requirements.txt
check $? "pandas 2.0+ specified"
grep -q "numpy>=1.24.0" requirements.txt
check $? "numpy 1.24+ specified"
grep -q "scikit-learn>=1.3.0" requirements.txt
check $? "scikit-learn 1.3+ specified"
grep -q "plotly>=5.17.0" requirements.txt
check $? "plotly 5.17+ specified"

# Summary
echo ""
echo "========================================"
echo "Verification Complete"
echo "========================================"
echo "Checks passed: $checks_passed / $checks_total"
echo ""

if [ $checks_passed -eq $checks_total ]; then
    echo -e "${GREEN}✓ All checks passed! Modernization successful.${NC}"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please review above.${NC}"
    exit 1
fi
