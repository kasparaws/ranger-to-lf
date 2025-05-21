#!/usr/bin/env python3
"""
Convert all Ranger policy JSON files in a folder into AWS Lake Formation
CloudFormation templates, without using YAML anchors/aliases.

Usage:
    python ranger_to_lf_converter.py --policies-dir policies --output-dir output
"""
import json
import yaml
import argparse
import os
import glob
import sys

# Custom Dumper to disable YAML aliases
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

# Map Ranger actions to Lake Formation permissions
ACTION_MAP = {
    "select": "SELECT",
    "insert": "INSERT",
    "update": "ALTER",
    "delete": "DELETE",
    "create": "CREATE_TABLE",
    "drop": "DROP",
    "alter": "ALTER"
}

def parse_policy(policy):
    db = policy.get("database", "UNKNOWN_DB")
    tbl = policy.get("table", policy.get("resourcePath", "UNKNOWN_TABLE")).split("/")[-1]
    principals = []
    for u in policy.get("users", []):
        principals.append({"DataLakePrincipalIdentifier": u})
    for g in policy.get("groups", []):
        principals.append({"DataLakePrincipalIdentifier": g})
    perms = [ACTION_MAP[a.lower()] for a in policy.get("permissions", []) if a.lower() in ACTION_MAP]
    return db, tbl, principals, perms


def build_cfn(policies):
    tpl = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "Lake Formation permissions generated from Ranger",
        "Resources": {}
    }
    for i, pol in enumerate(policies):
        db, tbl, principals, perms = parse_policy(pol)
        for p in principals:
            logical_id = f"LFPerm{i}_{p['DataLakePrincipalIdentifier'].replace('-', '_')}"
            tpl["Resources"][logical_id] = {
                "Type": "AWS::LakeFormation::Permissions",
                "Properties": {
                    "DataLakePrincipal": p,
                    "Resource": {
                        "Table": {
                            "CatalogId": {"Ref": "AWS::AccountId"},
                            "DatabaseName": db,
                            "Name": tbl
                        }
                    },
                    "Permissions": perms
                }
            }
    return tpl


def main():
    parser = argparse.ArgumentParser(description='Convert Ranger JSON policies directory to Lake Formation CFN templates')
    parser.add_argument('--policies-dir', '-p', default='policies', help='Directory containing Ranger JSON policy files')
    parser.add_argument('--output-dir', '-o', default='output', help='Directory to write CFN YAML outputs')
    args = parser.parse_args()

    if not os.path.isdir(args.policies_dir):
        sys.exit(f"Policies directory not found: {args.policies_dir}")
    os.makedirs(args.output_dir, exist_ok=True)

    json_files = glob.glob(os.path.join(args.policies_dir, '*.json'))
    if not json_files:
        print(f"No JSON files found in {args.policies_dir}")
        return

    for json_file in json_files:
        with open(json_file) as f:
            data = json.load(f)
        policies = data.get('policies', data)
        cfn = build_cfn(policies)
        base = os.path.splitext(os.path.basename(json_file))[0]
        out_path = os.path.join(args.output_dir, f"{base}.yml")
        # Write without aliases
        with open(out_path, 'w') as f:
            yaml.dump(cfn, f, Dumper=NoAliasDumper, default_flow_style=False)
        print(f"Wrote CloudFormation → {out_path}")

if __name__ == "__main__":
    main()
