import os
import shutil
from pathlib import Path

base_dir = Path("D:/MASrepos/deepagents-langchain/libs/deepagents-web/services/deepagents_data/models")
nested_dir = base_dir / "models"

# 1. Move everything from nested_dir to base_dir
if nested_dir.exists():
    for item in nested_dir.iterdir():
        dest = base_dir / item.name
        if dest.exists():
            if dest.is_dir():
                shutil.rmtree(dest)
            else:
                dest.unlink()
        shutil.move(str(item), str(base_dir))
    nested_dir.rmdir()

# 2. Fix MFD structure
mfd_dir = base_dir / "MFD"
yolo_dir = mfd_dir / "YOLO"
weights_file = mfd_dir / "weights.pt"
target_file = yolo_dir / "yolo_v8_ft.pt"

if weights_file.exists():
    yolo_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(weights_file), str(target_file))
    print(f"Moved {weights_file} to {target_file}")
else:
    print(f"{weights_file} not found")

# 3. Check layout config
layout_dir = base_dir / "Layout"
if layout_dir.exists():
    print("Layout models present")

# 4. Check TabRec
tabrec_dir = base_dir / "TabRec"
if tabrec_dir.exists():
    print("TabRec models present")
