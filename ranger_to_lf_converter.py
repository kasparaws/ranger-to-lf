#!/usr/bin/env python3
"""
Convert all Ranger policy JSON files in a folder into AWS Lake Formation
CloudFormation templates, supporting:
  - Custom AWS account ID
  - Principal ARNs via template
  - Optional overrides for databases, tables, and groups
  - No YAML aliases and valid logical IDs

Usage:
    python ranger_to_lf_converter.py \
      --config config.yml \
      --policies-dir policies \
      --output-dir output

Example `config.yml` keys:
```yaml
# AWS account ID for CatalogId
account_id: "123456789012"

# ARN template, {account} and {principal} placeholders
principal_arn_template: "arn:aws:iam::{account}:role/{principal}"

# Default database if missing
default_database: "default_db"

# Override specific source database names to target
database_overrides:
  sales: "sales_prod"
  marketing: "marketing_prod"

# Override specific source table names to target
table_overrides:
  test: "target_table"
  metrics: "sales_metrics_prod"

# Override specific source group names to different principal ID
# e.g. map 'analysts' -> 'Admin'
group_overrides:
  analysts: "Admin"
  hcp_team: "HCPAccessRole"
```
"""
import json
import yaml
import argparse
import os
import glob
import sys
import re

# Disable YAML aliases
class NoAliasDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

# Ranger action -> Lake Formation permission
ACTION_MAP = {
    "select": "SELECT",
    "insert": "INSERT",
    "update": "ALTER",
    "delete": "DELETE",
    "create": "CREATE_TABLE",
    "drop": "DROP",
    "alter": "ALTER"
}

def load_config(path):
    if not os.path.isfile(path):
        sys.exit(f"Config file not found: {path}")
    with open(path) as f:
        cfg = yaml.safe_load(f)
    # Required
    for key in ("account_id", "principal_arn_template"): 
        if key not in cfg:
            sys.exit(f"Missing '{key}' in config")
    # Optional overrides
    cfg.setdefault("default_database", None)
    cfg.setdefault("database_overrides", {})
    cfg.setdefault("table_overrides", {})
    cfg.setdefault("group_overrides", {})
    return cfg


def parse_policy(policy, cfg):
    # Database override
    db = policy.get("database") or cfg.get("default_database") or "UNKNOWN_DB"
    db = cfg["database_overrides"].get(db, db)
    # Table override
    tbl_raw = policy.get("table", policy.get("resourcePath", "UNKNOWN_TABLE")).split("/")[-1]
    tbl = cfg["table_overrides"].get(tbl_raw, tbl_raw)

    principals = []
    # Users: no group override
    for u in policy.get("users", []):
        principals.append(u)
    # Groups: apply override mapping if present
    for g in policy.get("groups", []):
        mapped = cfg["group_overrides"].get(g, g)
        principals.append(mapped)

    # Build ARN and perms
    perm_list = [ACTION_MAP[a.lower()] for a in policy.get("permissions", []) if a.lower() in ACTION_MAP]
    principal_objs = [
        {"DataLakePrincipalIdentifier": cfg["principal_arn_template"].format(account=cfg["account_id"], principal=who)}
        for who in principals
    ]
    return db, tbl, principal_objs, perm_list


def build_cfn(policies, cfg):
    tpl = {
        "AWSTemplateFormatVersion": "2010-09-09",
        "Description": "Lake Formation permissions generated from Ranger",
        "Resources": {}
    }
    for i, pol in enumerate(policies):
        db, tbl, principals, perms = parse_policy(pol, cfg)
        for p in principals:
            # Create valid logical ID
            principal_id = p['DataLakePrincipalIdentifier'].split('/')[-1]
            parts = re.split(r'[^0-9a-zA-Z]+', principal_id)
            token = ''.join(part.capitalize() for part in parts if part)
            logical_id = f"LFPerm{i}{token}{tbl.capitalize()}"
            tpl["Resources"][logical_id] = {
                "Type": "AWS::LakeFormation::Permissions",
                "Properties": {
                    "DataLakePrincipal": p,
                    "Resource": {
                        "TableResource": {
                            "CatalogId": cfg["account_id"],
                            "DatabaseName": db,
                            "Name": tbl
                        }
                    },
                    "Permissions": perms
                }
            }
    return tpl


def main():
    parser = argparse.ArgumentParser(description='Convert Ranger JSON policies to LF CFN with overrides')
    parser.add_argument('--config', '-c', required=True, help='YAML config path')
    parser.add_argument('--policies-dir', '-p', default='policies', help='Dir with Ranger JSONs')
    parser.add_argument('--output-dir', '-o', default='output', help='Dir for generated CFN YAMLs')
    args = parser.parse_args()

    cfg = load_config(args.config)
    policies_dir = args.policies_dir
    output_dir = args.output_dir

    if not os.path.isdir(policies_dir):
        sys.exit(f"Policies directory not found: {policies_dir}")
    os.makedirs(output_dir, exist_ok=True)

    files = glob.glob(os.path.join(policies_dir, '*.json'))
    if not files:
        print(f"No JSON files in {policies_dir}")
        return

    for path in files:
        with open(path) as f:
            data = json.load(f)
        policies = data.get('policies', data)
        cfn = build_cfn(policies, cfg)
        base = os.path.splitext(os.path.basename(path))[0]
        out_file = os.path.join(output_dir, f"{base}.yml")
        with open(out_file, 'w') as f:
            yaml.dump(cfn, f, Dumper=NoAliasDumper, default_flow_style=False)
        print(f"Written CFN → {out_file}")

if __name__ == "__main__":
    main()
