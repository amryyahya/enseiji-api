from importlib.metadata import distributions, PackageNotFoundError

with open("requirements.txt") as f:
    packages = [line.strip() for line in f if line.strip()]

def get_installed_version(package_name):
    try:
        for dist in distributions():
            if dist.metadata['Name'].lower() == package_name.lower():
                return dist.version
        return None
    except PackageNotFoundError:
        return None

for package in packages:
    version = get_installed_version(package)
    if version:
        print(f"{package}=={version}")
    else:
        print(f"{package} not installed")
