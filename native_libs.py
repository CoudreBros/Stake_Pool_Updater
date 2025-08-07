import os
import subprocess
import shutil
from spu_helpers import ask_user_to_continue, clear_terminal, print_header, resolve_path

GIT_DIR = resolve_path("GIT_DIR", default="~/git")

def check_lib_exists(libfile, headerfile):
    lib_path = f"/usr/local/lib/{libfile}"
    header_path = f"/usr/local/include/{headerfile}"
    return os.path.exists(lib_path) and os.path.exists(header_path)

def check_lmdb_installed():
    try:
        subprocess.run(["dpkg", "-s", "liblmdb-dev"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def install_lmdb():
    print("\n⬇️ Installing liblmdb-dev...")
    try:
        subprocess.run(["sudo", "apt", "update"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y", "liblmdb-dev"], check=True)
        print("✅ liblmdb-dev installed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install liblmdb-dev: {e}")

def safe_git_clone(repo_url, dest_folder_name):
    """
    Clones a git repository into GIT_DIR, deleting the folder if it already exists and user agrees.
    """
    dest_path = os.path.join(GIT_DIR, dest_folder_name)
    if os.path.exists(dest_path):
        print(f"\n⚠️  Folder '{dest_folder_name}' already exists in {GIT_DIR}.")
        if ask_user_to_continue("Do you want to delete and clone again?"):
            try:
                shutil.rmtree(dest_path)
                print(f"🧹 Deleted {dest_path}")
            except Exception as e:
                print(f"❌ Failed to delete folder: {e}")
                return False
        else:
            print(f"⏭️  Skipping clone of {dest_folder_name}.")
            return False

    try:
        subprocess.run(["git", "clone", repo_url], cwd=GIT_DIR, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Git clone failed: {e}")
        return False

def check_native_libs():
    print("🔍 Checking required native libraries...\n")

    libs = [
        ("libsodium", "libsodium.a", "sodium.h"),
        ("secp256k1", "libsecp256k1.a", "secp256k1.h"),
        ("blst", "libblst.a", "blst.h"),
    ]

    missing = []

    for name, libfile, headerfile in libs:
        ok = check_lib_exists(libfile, headerfile)
        status = "✅ Found" if ok else "❌ Missing"
        print(f"{name:<12}: {status}")
        if not ok:
            missing.append(name)

    lmdb_ok = check_lmdb_installed()
    print(f"{'liblmdb-dev':<12}: {'✅ Installed' if lmdb_ok else '❌ Missing'}")
    if not lmdb_ok:
        missing.append("liblmdb-dev")

    return missing

def install_libsodium():
    print("\n⬇️ Installing libsodium...")
    os.makedirs(GIT_DIR, exist_ok=True)
    if not safe_git_clone("https://github.com/input-output-hk/libsodium", "libsodium"):
        return
    try:
        subprocess.run(["git", "checkout", "dbb48cc"], cwd=f"{GIT_DIR}/libsodium", check=True)
        subprocess.run(["./autogen.sh"], cwd=f"{GIT_DIR}/libsodium", check=True)
        subprocess.run(["./configure"], cwd=f"{GIT_DIR}/libsodium", check=True)
        subprocess.run(["make"], cwd=f"{GIT_DIR}/libsodium", check=True)
        subprocess.run(["make", "check"], cwd=f"{GIT_DIR}/libsodium", check=True)
        subprocess.run(["sudo", "make", "install"], cwd=f"{GIT_DIR}/libsodium", check=True)
        print("✅ libsodium installed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ libsodium install failed: {e}")

def install_secp256k1():
    print("\n⬇️ Installing secp256k1...")
    os.makedirs(GIT_DIR, exist_ok=True)
    if not safe_git_clone("https://github.com/bitcoin-core/secp256k1", "secp256k1"):
        return
    try:
        subprocess.run(["./autogen.sh"], cwd=f"{GIT_DIR}/secp256k1", check=True)
        subprocess.run(["./configure", "--enable-module-schnorrsig", "--enable-experimental"], cwd=f"{GIT_DIR}/secp256k1", check=True)
        subprocess.run(["make"], cwd=f"{GIT_DIR}/secp256k1", check=True)
        subprocess.run(["make", "check"], cwd=f"{GIT_DIR}/secp256k1", check=True)
        subprocess.run(["sudo", "make", "install"], cwd=f"{GIT_DIR}/secp256k1", check=True)
        subprocess.run(["sudo", "ldconfig"], check=True)
        print("✅ secp256k1 installed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ secp256k1 install failed: {e}")

def install_blst():
    print("\n⬇️ Installing blst...")
    os.makedirs(GIT_DIR, exist_ok=True)
    if not safe_git_clone("https://github.com/supranational/blst", "blst"):
        return
    try:
        subprocess.run(["git", "checkout", "v0.3.11"], cwd=f"{GIT_DIR}/blst", check=True)
        subprocess.run(["./build.sh"], cwd=f"{GIT_DIR}/blst", check=True)

        pc_content = f"""prefix=/usr/local
exec_prefix=${{prefix}}
libdir=${{exec_prefix}}/lib
includedir=${{prefix}}/include

Name: libblst
Description: Multilingual BLS12-381 signature library
URL: https://github.com/supranational/blst
Version: 0.3.11
Cflags: -I${{includedir}}
Libs: -L${{libdir}} -lblst
"""
        with open(f"{GIT_DIR}/blst/libblst.pc", "w") as f:
            f.write(pc_content)

        subprocess.run(["sudo", "cp", "libblst.pc", "/usr/local/lib/pkgconfig/"], cwd=f"{GIT_DIR}/blst", check=True)
        subprocess.run(["sudo", "cp", "bindings/blst_aux.h", "bindings/blst.h", "bindings/blst.hpp", "/usr/local/include/"], cwd=f"{GIT_DIR}/blst", check=True)
        subprocess.run(["sudo", "cp", "libblst.a", "/usr/local/lib"], cwd=f"{GIT_DIR}/blst", check=True)

        subprocess.run([
            "sudo", "chmod", "u=rw,go=r",
            "/usr/local/lib/libblst.a",
            "/usr/local/lib/pkgconfig/libblst.pc",
            "/usr/local/include/blst.h",
            "/usr/local/include/blst.hpp",
            "/usr/local/include/blst_aux.h"
        ], check=True)

        print("✅ blst installed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ blst install failed: {e}")

def check_and_install_libs():
    """Main logic for checking and optionally installing required libraries."""
    clear_terminal()
    print_header("Check & install required native libraries")
    print()

    missing = check_native_libs()

    if not missing:
        print("\n✅ All required libraries are installed.")
        return

    print("\n❗ Some libraries are missing:")
    for lib in missing:
        print(f" - {lib}")

    if not ask_user_to_continue("Do you want to install missing libraries now?"):
        print("➡️  Skipping library installation.")
        return

    if "libsodium" in missing:
        install_libsodium()
    if "secp256k1" in missing:
        install_secp256k1()
    if "blst" in missing:
        install_blst()
    if "liblmdb-dev" in missing:
        install_lmdb()

    print("\n➡️  Library installation completed.")
