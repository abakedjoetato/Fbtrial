import os

# Read requirements.txt
with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()

# Remove empty lines and comments
requirements = [r.strip() for r in requirements if r.strip() and not r.strip().startswith('#')]

# Normalize package names (remove version constraints)
clean_packages = []
for req in requirements:
    # Split package name from version constraint
    package = req.split('==')[0].split('>=')[0].split('<=')[0].split('<')[0].split('>')[0].split('~=')[0].strip()
    clean_packages.append(package)

# Remove duplicates while preserving order
unique_packages = []
for package in clean_packages:
    if package.lower() not in [p.lower() for p in unique_packages]:
        unique_packages.append(package)

# Write cleaned requirements to a new file
with open('requirements_clean_new.txt', 'w') as f:
    for package in unique_packages:
        f.write(package + '\n')

print(f"Cleaned {len(requirements)} requirements down to {len(unique_packages)} unique packages")
print("Unique packages:")
for package in unique_packages:
    print(f"- {package}")