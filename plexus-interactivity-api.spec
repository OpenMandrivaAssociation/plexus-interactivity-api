Name:		plexus-interactivity-api
Version:	1.6.0
Release:	1
Summary:	Reads and writes interactive command-line prompts
Group:		Development/Java
License:	MIT
URL:		https://github.com/codehaus-plexus/plexus-interactivity
Source0:	https://github.com/codehaus-plexus/plexus-interactivity/archive/refs/tags/plexus-interactivity-%{version}.tar.gz#/plexus-interactivity-%{version}.tar.gz
BuildArch:	noarch
BuildRequires:	python
BuildRequires:	maven
BuildRequires:	maven-components >= 3.10.0
BuildRequires:	java-current-devel
BuildRequires:	mvn(javax.inject:javax.inject)
# javax.inject and jakarta-inject both provide this coordinate.
BuildRequires:	javax.inject >= 1-2
Requires:	javax.inject >= 1-2
BuildSystem:	maven
BuildOption(install):	--file-name %{name}

%description
Reads lines and passwords from an interactive console and writes
prompts. Maven plugins such as help:evaluate inject InputHandler from
this jar. 1.6.0 is the current release. The optional JLine handler
needs JLine 3.30, which is not packaged, so this build keeps the
plain console handler. Tests need JUnit Jupiter and Guice, so they
are not run.

%prep
%autosetup -n plexus-interactivity-plexus-interactivity-%{version}
rm -rf .github src plexus-interactivity-api/src/test
rm -rf plexus-interactivity-api/src/main/java/org/codehaus/plexus/components/interactivity/jline
mkdir -p src
mv plexus-interactivity-api/src/main src/main
rm -rf plexus-interactivity-api
python - <<'PY'
import re
from pathlib import Path

header = Path("src/main/java/org/codehaus/plexus/components/interactivity/InputHandler.java").read_text(encoding="utf-8")
start = header.find("/*")
end = header.find("*/", start)
lines = []
for line in header[start + 2:end].splitlines():
    line = line.strip()
    if line.startswith("*"):
        line = line[1:].lstrip()
    lines.append(line)
Path("LICENSE").write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

root = Path("src/main/java")
names = []
for path in sorted(root.rglob("*.java")):
    text = path.read_text(encoding="utf-8", errors="replace")
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    text = re.sub(r"//.*?$", "", text, flags=re.M)
    match = re.search(r"\b(?:class|interface|enum)\s+([A-Za-z0-9_]+)", text)
    if not match or "@Named" not in text[:match.start()]:
        continue
    pkg = re.search(r"(?m)^package\s+([A-Za-z0-9_.]+)\s*;", text)
    if pkg:
        names.append(pkg.group(1) + "." + match.group(1))
if len(names) != 3:
    raise SystemExit("expected three @Named classes, got " + str(names))
dest = Path("src/main/resources/META-INF/sisu")
dest.mkdir(parents=True)
(dest / "javax.inject.Named").write_text("\n".join(names) + "\n", encoding="utf-8")
PY
python - <<'PY'
import xml.etree.ElementTree as ET

NS = "http://maven.apache.org/POM/4.0.0"
ET.register_namespace("", NS)

def tag(name):
    return "{" + NS + "}" + name

def add(parent, name, text):
    node = ET.SubElement(parent, tag(name))
    node.text = text
    return node

root = ET.Element(tag("project"))
add(root, "modelVersion", "4.0.0")
add(root, "groupId", "org.codehaus.plexus")
add(root, "artifactId", "plexus-interactivity-api")
add(root, "version", "%{version}")
add(root, "name", "Plexus Interactivity API")
props = ET.SubElement(root, tag("properties"))
add(props, "maven.compiler.release", "8")
add(props, "project.build.sourceEncoding", "UTF-8")
deps = ET.SubElement(root, tag("dependencies"))
dep = ET.SubElement(deps, tag("dependency"))
add(dep, "groupId", "javax.inject")
add(dep, "artifactId", "javax.inject")
add(dep, "version", "1")
add(dep, "scope", "provided")
ET.ElementTree(root).write("pom.xml", encoding="utf-8", xml_declaration=True)
PY

%files -f .mfiles
%doc LICENSE README.md
