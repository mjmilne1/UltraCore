# -*- coding: utf-8 -*-
"""Quick activation of MCP and Agents"""

# Create __init__.py files to make packages importable
import os

dirs = [
    "src/ultracore/mcp",
    "src/ultracore/agents"
]

for dir_path in dirs:
    init_file = os.path.join(dir_path, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, 'w') as f:
            f.write("")
        print(f"Created {init_file}")

print("Package initialization files created!")
