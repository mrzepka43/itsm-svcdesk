# ai-generated: 100% - Copilot implemented the matching rules from CI-SPEC.md
"""Compute scanner confusion matrices from labels and SARIF."""

from __future__ import annotations

import argparse
import json
import re
import sys
from urllib.parse import unquote


CLASS_CWES = {
    "secret": {259, 260, 321, 798},
    "injection": {74, 77, 78, 79, 80, 88, 89, 90, 91, 94, 95, 96, 611, 776, 917, 943, 1336},
    "deserialization": {502},
    "weak-crypto": {261, 326, 327, 328, 330, 331, 338, 759, 760, 916},
    "insecure-transport": {295, 297, 319, 322, 757},
    "path-traversal": {22, 23, 35, 36, 73},
    "ssrf": {918},
    "vulnerable-dependency": {937, 1035, 1104, 1395},
    "misconfiguration": {16, 215, 250, 489, 668, 732, 1188},
    "access-control": {284, 285, 639, 862, 863},
}


def object_or_empty(value):
    return value if isinstance(value, dict) else {}


def array_or_empty(value):
    return value if isinstance(value, list) else []


def tags(value):
    properties = object_or_empty(object_or_empty(value).get("properties"))
    return [tag for tag in array_or_empty(properties.get("tags")) if isinstance(tag, str)]


def tool_id(driver):
    name = driver.get("name")
    if not isinstance(name, str):
        return "unknown"
    name = name.strip().lower()
    if name in {"semgrep", "semgrep oss", "semgrep ce", "semgrep community edition", "semgrep pro"}:
        return "semgrep"
    return re.sub(r"[^a-z0-9]+", "-", name).strip("-") or "unknown"


def result_classes(result, driver, tool):
    properties = object_or_empty(result.get("properties"))
    explicit = properties.get("class")
    if isinstance(explicit, str) and explicit in CLASS_CWES:
        return {explicit}

    if tool == "gitleaks":
        return {"secret"}
    if tool in {"grype", "osv-scanner"}:
        return {"vulnerable-dependency"}

    rule_id = result.get("ruleId")
    rule = {}
    if isinstance(rule_id, str):
        for candidate in array_or_empty(driver.get("rules")):
            if isinstance(candidate, dict) and candidate.get("id") == rule_id:
                rule = candidate
                break
    rule_tags = tags(rule)
    if tool == "trivy":
        trivy_classes = {
            "vulnerability": "vulnerable-dependency",
            "secret": "secret",
            "misconfiguration": "misconfiguration",
        }
        found = {trivy_classes[tag.lower()] for tag in rule_tags if tag.lower() in trivy_classes}
        if found:
            return found

    cwes = set()
    for tag in tags(result) + rule_tags:
        cwes.update(int(match) for match in re.findall(r"(?<![A-Za-z0-9])CWE-([0-9]+)", tag, re.IGNORECASE))
    return {name for name, numbers in CLASS_CWES.items() if cwes & numbers} or {"other"}


def location(result, set_root):
    locations = array_or_empty(result.get("locations"))
    if not locations:
        return None
    physical = object_or_empty(object_or_empty(locations[0]).get("physicalLocation"))
    artifact = object_or_empty(physical.get("artifactLocation"))
    uri = artifact.get("uri")
    if not isinstance(uri, str) or not uri:
        return None
    path = unquote(uri)
    if path[:7].lower() == "file://":
        path = path[7:]
    if path.startswith("./"):
        path = path[2:]
    components = path.split("/")
    if set_root not in components:
        return None
    index = len(components) - 1 - components[::-1].index(set_root)
    filename = "/".join(components[index:])

    region = object_or_empty(physical.get("region"))
    start = region.get("startLine")
    if type(start) is not int or start < 1:
        return filename, None, None
    end = region.get("endLine")
    if type(end) is not int or end < start:
        end = start
    return filename, start, end


def package_tokens(result):
    message = object_or_empty(result.get("message"))
    text = message.get("text")
    if not isinstance(text, str):
        return set()
    return {
        re.sub(r"[-_.]+", "-", token.strip("-_.").lower())
        for token in re.findall(r"[A-Za-z0-9._-]+", text)
        if token.strip("-_.")
    }


def matches(defect, filename, start, end, classes, packages):
    if defect["file"] != filename or defect["class"] not in classes:
        return False
    if defect["class"] == "vulnerable-dependency":
        package = re.sub(r"[-_.]+", "-", defect["package"].lower())
        return package in packages
    return start is not None and start <= defect["end_line"] and defect["start_line"] <= end


def confusion_matrix(labels, sarif_documents):
    defects = labels["defects"]
    tools = {}
    for document in sarif_documents:
        for run in array_or_empty(object_or_empty(document).get("runs")):
            if not isinstance(run, dict):
                continue
            driver = object_or_empty(object_or_empty(run.get("tool")).get("driver"))
            tool = tool_id(driver)
            found, false_positives = tools.setdefault(tool, (set(), set()))
            for result in array_or_empty(run.get("results")):
                if not isinstance(result, dict):
                    continue
                if result.get("kind") not in (None, "fail") or result.get("suppressions"):
                    continue
                place = location(result, labels["set"])
                if place is None:
                    continue
                filename, start, end = place
                classes = result_classes(result, driver, tool)
                packages = package_tokens(result) if "vulnerable-dependency" in classes else set()
                matched = {
                    index for index, defect in enumerate(defects)
                    if matches(defect, filename, start, end, classes, packages)
                }
                if matched:
                    found.update(matched)
                else:
                    rule_id = result.get("ruleId")
                    false_positives.add((rule_id if isinstance(rule_id, str) else None, filename, start, end))

    output = {}
    for tool, (found, false_positives) in tools.items():
        tp, fp, fn = len(found), len(false_positives), len(defects) - len(found)
        output[tool] = {
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "precision": round(tp / (tp + fp), 4) if tp + fp else None,
            "recall": round(tp / (tp + fn), 4) if tp + fn else None,
            "f1": round(2 * tp / (2 * tp + fp + fn), 4) if 2 * tp + fp + fn else None,
        }
    return {"set": labels["set"], "defects": len(defects), "tools": output}


def main(argv=None):
    parser = argparse.ArgumentParser(description="per-tool confusion matrix of SARIF against labels")
    parser.add_argument("--labels", required=True, help="labels JSON file")
    parser.add_argument("sarif", nargs="+", help="SARIF 2.1.0 files")
    args = parser.parse_args(argv)
    with open(args.labels, encoding="utf-8") as file:
        labels = json.load(file)
    documents = []
    for path in args.sarif:
        with open(path, encoding="utf-8") as file:
            documents.append(json.load(file))
    json.dump(confusion_matrix(labels, documents), sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
