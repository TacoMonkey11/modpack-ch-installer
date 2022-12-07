import json
import os
import platform
import subprocess
import urllib.request

import click


@click.group()
def cli():
    pass


@click.command()
@click.option('--curseforge', '-cf',
              help="Chooses whether or not to search for curseforge packs over FTB packs",
              prompt="Would you like to search for Curseforge packs instead of FTB?",
              type=click.BOOL,
              is_flag=True,
              default=False,
              show_default=False)
@click.option('--output', '-o',
              help="Chooses the directory to ionstall the server into",
              type=click.Path(exists=True, file_okay=False, dir_okay=True),
              prompt="Chose a directory to install the server into",
              default=".")
def install(curseforge, output):
    base_url = "https://api.modpacks.ch/public/curseforge/" if curseforge else "https://api.modpacks.ch/public/modpack/"

    pack_choices = search_packs(curseforge)

    pack_json_list = []
    for pack in pack_choices:
        pack_json = json.load(urllib.request.urlopen(f"{base_url}{pack}"))
        pack_json_list.append(pack_json)

    for pack in pack_json_list:
        click.echo(f"{pack_json_list.index(pack)} - {pack['name']}")

    pack_choice = click.prompt("Chose a modpack", type=click.IntRange(0, len(pack_choices) - 1))
    pack_choice_json = pack_json_list[pack_choice]

    version_choice = search_versions(pack_choice_json)
    installer_url = f"{base_url}{pack_choices[pack_choice]}/{pack_choice_json['versions'][version_choice]['id']}/server"
    installer_args = ["--auto", f"--path {output}"]
    if curseforge:
        installer_args.append("--curseforge")

    filename = f"{output}/serverinstall_{pack_choices[pack_choice]}_{pack_choice_json['versions'][version_choice]['id']}"

    download_installer(filename, installer_url, installer_args)


@click.command()
def update():
    base_url = "https://api.modpacks.ch/public/curseforge/" if os.path.exists(
        "manifest.json") else "https://api.modpacks.ch/public/modpack/"
    if not os.path.exists("version.json"):
        click.echo("Unable to locate the version.json file. Are you in the right directory?")
        exit(1)

    sorting_num = 0 if os.path.exists("manifest.json") else -1

    current_version = json.load(open("version.json"))
    latest_version = json.load(urllib.request.urlopen(f"{base_url}{current_version['parent']}"))["versions"][
        sorting_num]

    should_update = click.prompt(
        f"Current modpack version is {current_version['name']}, the latest is {latest_version['name']}. Would you like to update [y/N]",
        type=click.BOOL, show_default=False, default=False)
    if not should_update:
        exit(1)

    filename = f"serverinstall_{current_version['parent']}_{current_version['id']}"
    new_filename = f"serverinstall_{current_version['parent']}_{latest_version['id']}"
    if os.path.exists(filename):
        os.remove(filename)
    elif os.path.exists(filename + ".exe"):
        os.remove(filename + ".exe")
    installer_url = base_url + new_filename.replace("serverinstall_", "").replace("_", "/") + "/server"
    args = ["--auto"]
    if os.path.exists("manifest.json"):
        args.append("--curseforge")
    download_installer(new_filename, installer_url, args, ".")


def search_packs(curseforge: bool):
    packs = []
    # Get the search query from user
    search_query: str = click.prompt("Search for a modpack", type=click.STRING)
    search_query = search_query.replace(" ", "%20")

    # Send GET request with search query
    search_url = urllib.request.urlopen(f"https://api.modpacks.ch/public/modpack/search/5?term={search_query}")
    search_json = json.load(search_url)

    packs = search_json["curseforge"] if curseforge else search_json["packs"]

    return tuple(packs)


def search_versions(pack):
    for version in pack["versions"]:
        click.echo(f"{pack['versions'].index(version)} - {version['name']}")

    version_choice = click.prompt("Chose a version", type=click.IntRange(0, len(pack['versions']) - 1))
    return version_choice


def download_installer(filename, installer_url, args, output="."):
    os.chdir(output)
    if platform.system() == "Windows":
        filename += ".exe"
        urllib.request.urlretrieve(f"{installer_url}/windows", filename)
        args.insert(0, os.path.abspath(filename))
    elif platform.system() == "Linux" and platform.machine() == "aarch64":
        urllib.request.urlretrieve(f"{installer_url}/arm/linux", filename)
        args.insert(0, os.path.abspath(filename))
        subprocess.run(["chmod", "+x", f"./{filename}"])
    elif platform.system() == "Linux":
        urllib.request.urlretrieve(f"{installer_url}/linux", filename)
        args.insert(0, os.path.abspath(filename))
        subprocess.run(["chmod", "+x", f"./{filename}"])
    subprocess.run(args)


cli.add_command(install)
cli.add_command(update)
