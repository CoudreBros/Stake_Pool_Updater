import os
import shutil
import subprocess
from prompt_toolkit import prompt
from spu_helpers import ask_user_to_continue, clear_terminal, print_header, resolve_path

GIT_DIR = resolve_path("GIT_DIR", default="~/git")

DEFAULT_INSTALL_REFS = {
    "libsodium": "dbb48cc",
    "secp256k1": None,  # install default branch unless user overrides
    "blst": "v0.3.14",
}


def check_lib_exists(libfile, headerfile):
    lib_path = f"/usr/local/lib/{libfile}"
    header_path = f"/usr/local/include/{headerfile}"
    return os.path.exists(lib_path) and os.path.exists(header_path)


def check_lmdb_installed():
    try:
        subprocess.run(
            ["dpkg", "-s", "liblmdb-dev"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return True
    except subprocess.CalledProcessError:
        return False


def get_pkg_config_version(pkg_name):
    """Return version string from pkg-config, or None if unavailable."""
    try:
        result = subprocess.run(
            ["pkg-config", "--modversion", pkg_name],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or None
    except subprocess.CalledProcessError:
        return None


def get_lmdb_version():
    try:
        version_output = subprocess.run(
            ["dpkg-query", "-W", "-f=${Version}", "liblmdb-dev"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return version_output or None
    except subprocess.CalledProcessError:
        return None


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
        ("libsodium", "libsodium.a", "sodium.h", "libsodium"),
        ("secp256k1", "libsecp256k1.a", "secp256k1.h", "libsecp256k1"),
        ("blst", "libblst.a", "blst.h", "libblst"),
    ]

    results = []

    for name, libfile, headerfile, pkg_name in libs:
        ok = check_lib_exists(libfile, headerfile)
        version = get_pkg_config_version(pkg_name) if ok else None
        status = "✅ Found" if ok else "❌ Missing"
        version_note = f" (version: {version})" if version else ""
        print(f"{name:<12}: {status}{version_note}")
        results.append({"name": name, "installed": ok, "version": version})

    lmdb_ok = check_lmdb_installed()
    lmdb_version = get_lmdb_version() if lmdb_ok else None
    lmdb_status = "✅ Installed" if lmdb_ok else "❌ Missing"
    print(f"{'liblmdb-dev':<12}: {lmdb_status}" + (f" (version: {lmdb_version})" if lmdb_version else ""))
    results.append({"name": "liblmdb-dev", "installed": lmdb_ok, "version": lmdb_version})

    return results


def install_libsodium(ref=DEFAULT_INSTALL_REFS["libsodium"]):
    print("\n⬇️ Installing libsodium...")
    os.makedirs(GIT_DIR, exist_ok=True)
    if not safe_git_clone("https://github.com/input-output-hk/libsodium", "libsodium"):
        return
    try:
        if ref:
            subprocess.run(["git", "checkout", ref], cwd=f"{GIT_DIR}/libsodium", check=True)
        subprocess.run(["./autogen.sh"], cwd=f"{GIT_DIR}/libsodium", check=True)
        subprocess.run(["./configure"], cwd=f"{GIT_DIR}/libsodium", check=True)
        subprocess.run(["make"], cwd=f"{GIT_DIR}/libsodium", check=True)
        subprocess.run(["make", "check"], cwd=f"{GIT_DIR}/libsodium", check=True)
        subprocess.run(["sudo", "make", "install"], cwd=f"{GIT_DIR}/libsodium", check=True)
        print("✅ libsodium installed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ libsodium install failed: {e}")


def install_secp256k1(ref=DEFAULT_INSTALL_REFS["secp256k1"]):
    print("\n⬇️ Installing secp256k1...")
    os.makedirs(GIT_DIR, exist_ok=True)
    if not safe_git_clone("https://github.com/bitcoin-core/secp256k1", "secp256k1"):
        return
    try:
        if ref:
            subprocess.run(["git", "checkout", ref], cwd=f"{GIT_DIR}/secp256k1", check=True)
        subprocess.run(["./autogen.sh"], cwd=f"{GIT_DIR}/secp256k1", check=True)
        subprocess.run(
            ["./configure", "--enable-module-schnorrsig", "--enable-experimental"],
            cwd=f"{GIT_DIR}/secp256k1",
            check=True,
        )
        subprocess.run(["make"], cwd=f"{GIT_DIR}/secp256k1", check=True)
        subprocess.run(["make", "check"], cwd=f"{GIT_DIR}/secp256k1", check=True)
        subprocess.run(["sudo", "make", "install"], cwd=f"{GIT_DIR}/secp256k1", check=True)
        subprocess.run(["sudo", "ldconfig"], check=True)
        print("✅ secp256k1 installed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ secp256k1 install failed: {e}")


def install_blst(ref=DEFAULT_INSTALL_REFS["blst"]):
    print("\n⬇️ Installing blst...")
    os.makedirs(GIT_DIR, exist_ok=True)
    if not safe_git_clone("https://github.com/supranational/blst", "blst"):
        return
    try:
        if ref:
            subprocess.run(["git", "checkout", ref], cwd=f"{GIT_DIR}/blst", check=True)
        subprocess.run(["./build.sh"], cwd=f"{GIT_DIR}/blst", check=True)

        version_label = ref.lstrip("v") if ref else "unknown"
        pc_content = f"""prefix=/usr/local
exec_prefix=${{prefix}}
libdir=${{exec_prefix}}/lib
includedir=${{prefix}}/include

Name: libblst
Description: Multilingual BLS12-381 signature library
URL: https://github.com/supranational/blst
Version: {version_label}
Cflags: -I${{includedir}}
Libs: -L${{libdir}} -lblst
"""
        with open(f"{GIT_DIR}/blst/libblst.pc", "w") as f:
            f.write(pc_content)

        subprocess.run(["sudo", "cp", "libblst.pc", "/usr/local/lib/pkgconfig/"], cwd=f"{GIT_DIR}/blst", check=True)
        subprocess.run(
            ["sudo", "cp", "bindings/blst_aux.h", "bindings/blst.h", "bindings/blst.hpp", "/usr/local/include/"],
            cwd=f"{GIT_DIR}/blst",
            check=True,
        )
        subprocess.run(["sudo", "cp", "libblst.a", "/usr/local/lib"], cwd=f"{GIT_DIR}/blst", check=True)

        subprocess.run(
            [
                "sudo",
                "chmod",
                "u=rw,go=r",
                "/usr/local/lib/libblst.a",
                "/usr/local/lib/pkgconfig/libblst.pc",
                "/usr/local/include/blst.h",
                "/usr/local/include/blst.hpp",
                "/usr/local/include/blst_aux.h",
            ],
            check=True,
        )

        print("✅ blst installed.")
    except subprocess.CalledProcessError as e:
        print(f"❌ blst install failed: {e}")


def prompt_for_version(lib_name, current_version, default_ref):
    """Ask user for git tag/commit to use when reinstalling."""
    version_text = current_version or "unknown"
    default_hint = f" [{default_ref}]" if default_ref else ""
    user_input = prompt(
        f"Enter tag/commit to reinstall {lib_name} (current: {version_text}){default_hint}: "
    ).strip()
    if user_input:
        return user_input
    return default_ref


def check_and_install_libs():
    """Main logic for checking and optionally installing required libraries."""
    clear_terminal()
    print_header("Check & install required native libraries")
    print()

    libs_state = check_native_libs()
    missing = [lib["name"] for lib in libs_state if not lib["installed"]]

    if not missing:
        print("\n✅ All required libraries are installed.")
    else:
        print("\n❗ Some libraries are missing:")
        for lib in missing:
            print(f" - {lib}")

        if ask_user_to_continue("Do you want to install missing libraries now?"):
            if "libsodium" in missing:
                install_libsodium()
            if "secp256k1" in missing:
                install_secp256k1()
            if "blst" in missing:
                install_blst()
            if "liblmdb-dev" in missing:
                install_lmdb()
            print("\n➡️  Missing libraries installed.")
        else:
            print("➡️  Skipping library installation.")

    installed_libs = [lib for lib in libs_state if lib["installed"]]
    if installed_libs and ask_user_to_continue("\nDo you want to reinstall any library to a newer version?"):
        for lib in installed_libs:
            if not ask_user_to_continue(f"Reinstall {lib['name']} (current: {lib['version'] or 'unknown'})?"):
                continue

            ref = DEFAULT_INSTALL_REFS.get(lib["name"])
            if lib["name"] in ("libsodium", "secp256k1", "blst"):
                ref = prompt_for_version(lib["name"], lib["version"], ref)

            if lib["name"] == "libsodium":
                install_libsodium(ref)
            elif lib["name"] == "secp256k1":
                install_secp256k1(ref)
            elif lib["name"] == "blst":
                install_blst(ref)
            elif lib["name"] == "liblmdb-dev":
                install_lmdb()

    print("\n➡️  Library checks and updates completed.")
