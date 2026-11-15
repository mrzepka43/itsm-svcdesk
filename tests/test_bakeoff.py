# ai-generated: 100% - Copilot wrote focused tests for the course matching rules
import unittest

from bakeoff import confusion_matrix


def finding(uri, rule="r", start=1, **extra):
    physical = {"artifactLocation": {"uri": uri}}
    if start is not None:
        physical["region"] = {"startLine": start}
    return {"ruleId": rule, "locations": [{"physicalLocation": physical}], **extra}


def run(name, results, rules=None):
    return {"tool": {"driver": {"name": name, "rules": rules or []}}, "results": results}


class BakeoffTests(unittest.TestCase):
    def test_decoded_last_set_root_and_cwe_matching(self):
        labels = {"set": "set", "defects": [
            {"id": "a", "file": "set/a.py", "class": "injection", "start_line": 4, "end_line": 5},
            {"id": "b", "file": "set/a.py", "class": "injection", "start_line": 5, "end_line": 6},
        ]}
        rules = [{"id": "r", "properties": {"tags": ["external/cwe/CWE-089"]}}]
        result = finding("file:///set/ignored/%73et/a.py", start=5)
        output = confusion_matrix(labels, [{"runs": [run("Semgrep CE", [result], rules)]}])
        self.assertEqual((output["tools"]["semgrep"]["tp"], output["tools"]["semgrep"]["fn"]), (2, 0))

    def test_suppressions_first_location_invalid_lines_and_duplicate_fp(self):
        labels = {"set": "s", "defects": [
            {"id": "a", "file": "s/a.py", "class": "secret", "start_line": 1, "end_line": 1},
        ]}
        duplicate = finding("s/a.py", start=True)
        ignored = finding("s/a.py", suppressions=[None])
        second_location = {"locations": [{}, {"physicalLocation": {"artifactLocation": {"uri": "s/a.py"}}}]}
        output = confusion_matrix(labels, [{"runs": [
            run("gitleaks", [duplicate, duplicate, ignored, second_location, finding("s/a.py", kind="FAIL")])
        ]}])
        self.assertEqual(output["tools"]["gitleaks"], {
            "tp": 0, "fp": 1, "fn": 1, "precision": 0.0, "recall": 0.0, "f1": 0.0,
        })

    def test_dependency_tokens_ignore_lines_and_normalize_package(self):
        labels = {"set": "s", "defects": [
            {"id": "d", "file": "s/requirements.txt", "class": "vulnerable-dependency", "package": "my_pkg.name"},
        ]}
        result = finding("s/requirements.txt", start=None, message={"text": "Found My-Pkg_Name."})
        output = confusion_matrix(labels, [{"runs": [run("OSV-Scanner", [result])] }])
        self.assertEqual(output["tools"]["osv-scanner"]["tp"], 1)

    def test_explicit_class_overrides_tool_and_rule_tags(self):
        labels = {"set": "s", "defects": [
            {"id": "a", "file": "s/a.py", "class": "injection", "start_line": 1, "end_line": 1},
        ]}
        result = finding("s/a.py", properties={"class": "injection"})
        output = confusion_matrix(labels, [{"runs": [run("gitleaks", [result])]}])
        self.assertEqual(output["tools"]["gitleaks"]["tp"], 1)

    def test_unknown_run_empty_set_and_no_results(self):
        output = confusion_matrix({"set": "s", "defects": []}, [{"runs": [None, {"tool": {"driver": {"name": 9}}}]}])
        self.assertEqual(output["tools"]["unknown"], {
            "tp": 0, "fp": 0, "fn": 0, "precision": None, "recall": None, "f1": None,
        })


if __name__ == "__main__":
    unittest.main()
