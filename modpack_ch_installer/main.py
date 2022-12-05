import json
import os.path
import platform
import subprocess
import urllib.request

import click


@click.group()
def cli():
    pass


@click.command()
@click.option('--curseforge', '-cf',
              help="choose whether or not to search for curseforge packs",
              prompt="Would you like to search for Curseforge packs instead of FTB?",
              type=click.types.BOOL,
              is_flag=True,
              default=False,
              show_default=False)
def install(curseforge):
    search_query: str = click.prompt("Search for a modpack", type=click.types.STRING)
    search_query = search_query.replace(" ", "%20")

    search_url = urllib.request.urlopen(f"https://api.modpacks.ch/public/modpack/search/5?term={search_query}")
    search_json = json.load(search_url)

    if curseforge:
        pack_search_list = search_json["curseforge"]
        base_url = "https://api.modpacks.ch/public/curseforge/"
    else:
        pack_search_list = search_json["packs"]
        base_url = "https://api.modpacks.ch/public/modpack/"

    pack_json_list = []
    for pack in pack_search_list:
        pack_json = json.load(urllib.request.urlopen(f"{base_url}{pack}"))
        pack_json_list.append(pack_json)

    for pack in pack_json_list:
        click.echo(f"{pack_json_list.index(pack)} - {pack['name']}")

    modpack_choice = click.prompt("Chose a modpack", type=click.types.IntRange(0, len(pack_search_list) - 1))

    for version in pack_json_list[modpack_choice]['versions']:
        click.echo(f"{pack_json_list[modpack_choice]['versions'].index(version)} - {version['name']}")

    version_choice = click.prompt("Chose a version", type=click.types.IntRange(0, len(pack_json_list[modpack_choice]['versions']) - 1))

    installer_url = f"{base_url}{pack_search_list[modpack_choice]}/{pack_json_list[modpack_choice]['versions'][version_choice]['id']}/server"
    installer_args = ["--auto"]
    if curseforge:
        installer_args.append("--curseforge")

    filename = f"serverinstall_{pack_search_list[modpack_choice]}_{pack_json_list[modpack_choice]['versions'][version_choice]['id']}"

    if platform.system() == "Windows":
        filename += ".exe"
        urllib.request.urlretrieve(f"{installer_url}/windows", filename)
        installer_args.insert(0, filename)
    elif platform.system() == "Linux" and platform.machine() == "aarch64":
        urllib.request.urlretrieve(f"{installer_url}/arm/linux")
        installer_args.insert(0, filename)
        subprocess.run(["chmod", "+x", f"./{filename}"])
    elif platform.system() == "Linux":
        urllib.request.urlretrieve(f"{installer_url}/linux")
        installer_args.insert(0, filename)
        subprocess.run(["chmod", "+x", f"./{filename}"])

    subprocess.run(installer_args)


cli.add_command(install)
