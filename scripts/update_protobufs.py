import os
import re
import shutil
import stat
import subprocess
import sys
import logging
from typing import Any, Callable


def remove_readonly(function: Callable[[str], None], path: str, _: Any):
    os.chmod(path, stat.S_IWRITE)
    function(path)


def fetch_protobufs():
    if os.path.exists("temp_protobufs_repo"):
        shutil.rmtree("temp_protobufs_repo", onexc=remove_readonly)

    subprocess.run(["git", "clone", "--depth", "1",
                   "https://github.com/SteamDatabase/Protobufs.git", "temp_protobufs_repo"], check=True)

    if os.path.exists("protobufs"):
        shutil.rmtree("protobufs")

    os.makedirs("protobufs")

    source_directory = os.path.join("temp_protobufs_repo", "steam")

    for item in os.listdir(source_directory):
        source_path = os.path.join(source_directory, item)
        destination_path = os.path.join("protobufs", item)

        if os.path.isfile(source_path):
            shutil.copy2(source_path, destination_path)

    shutil.rmtree("temp_protobufs_repo", onexc=remove_readonly)


def fix_protobufs():
    protobufs_directory = "protobufs"
    files = os.listdir(protobufs_directory)
    renames: dict[str, str] = {}

    for filename in files:
        if not filename.endswith(".proto"):
            continue

        if filename.count(".") > 1:
            name_parts = filename.rsplit(".", 1)
            new_name = name_parts[0].replace(".", "_") + "." + name_parts[1]

            if filename != new_name:
                renames[filename] = new_name
                old_path = os.path.join(protobufs_directory, filename)
                new_path = os.path.join(protobufs_directory, new_name)
                os.rename(old_path, new_path)

    files = os.listdir(protobufs_directory)

    for filename in files:
        if not filename.endswith(".proto"):
            continue

        file_path = os.path.join(protobufs_directory, filename)

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        new_content = content

        if "syntax =" not in new_content and "edition =" not in new_content:
            new_content = 'syntax = "proto2";\n\n' + new_content

        for old_name, new_name in renames.items():
            new_content = new_content.replace(f'"{old_name}"', f'"{new_name}"')

        if new_content != content:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)


def compile_protobufs():
    source_protobufs_directory = os.path.join(
        "steam", "utils", "protobuf_manager", "protobufs")

    if os.path.exists(source_protobufs_directory):
        shutil.rmtree(source_protobufs_directory)

    os.makedirs(source_protobufs_directory)

    with open(os.path.join(source_protobufs_directory, "__init__.py"), "w"):
        pass

    proto_files = [file for file in os.listdir(
        "protobufs") if file.endswith(".proto")]
    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        "-I", "protobufs",
        f"--python_out={source_protobufs_directory}"
    ] + proto_files

    subprocess.run(cmd, check=True)


def generate_emsg_enum():
    input_file = os.path.join("protobufs", "enums_clientserver.proto")
    output_file = os.path.join("steam", "enums", "emsg.py")

    if not os.path.exists(input_file):
        logging.warning(f"{input_file} not found. Skipping EMsg generation.")
        return

    with open(input_file, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r"enum EMsg\s*\{([^}]*)\}", content, re.DOTALL)

    if not match:
        logging.warning("EMsg enum not found in enums_clientserver.proto")
        return

    enum_body = match.group(1)
    members: list[tuple[str, int]] = []
    pattern = re.compile(r"^\s*([a-zA-Z0-9_]+)\s*=\s*(\d+);", re.MULTILINE)

    for match in pattern.finditer(enum_body):
        name = match.group(1)

        if name.startswith("k_EMsg"):
            name = name[6:]

        value = int(match.group(2))
        members.append((name, value))

    lines = [
        "from enum import IntEnum",
        "",
        "",
        "class EMsg(IntEnum):",
    ]

    for name, value in members:
        lines.append(f"    {name} = {value}")

    lines.append("")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    fetch_protobufs()
    fix_protobufs()
    compile_protobufs()
    generate_emsg_enum()
