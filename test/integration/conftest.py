import sys
from pathlib import Path

# Add the project root directory to Python path
project_root = Path(__file__).parent.parent.parent
print(f"project_root: {project_root}")
sys.path.append(str(project_root))
