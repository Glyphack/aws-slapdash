import os
import re
from pathlib import Path
from types import new_class

SCRIPTS_DIR = Path(__file__).parent.absolute()
AWS_SLAPDASH_DIR = Path().parent / "aws_slapdash"

with open(SCRIPTS_DIR / "shared.py") as shared_code:
    code = (
        "# generated-begin\n"
        f"{shared_code.read().encode('unicode_escape').decode('utf-8')}"
        "# generated-end"
    )

    print(f"adding shared code to python files in {AWS_SLAPDASH_DIR}")
    with os.scandir(AWS_SLAPDASH_DIR) as it:
        for file in it:
            if (
                file.name.endswith(".py")
                and file.is_file
                and file.name not in ["__init__.py", "configure.py"]
            ):
                with open(file.path, "r") as service_code:
                    service_python_code = service_code.read()
                with open(file.path, "w") as service_code:
                    new_code = re.sub(
                        "# generated-begin.*?# generated-end",
                        code,
                        service_python_code,
                        flags=re.DOTALL,
                    )
                    service_code.write(new_code)
