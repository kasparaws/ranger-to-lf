# Ranger to Lake Formation Converter

This project provides a Python utility that converts Apache Ranger policy JSON files into an AWS Lake Formation CloudFormation template. The generated template defines corresponding Lake Formation permissions for tables in your data lake.

## Project Structure

```
ranger-to-lf/
├── .vscode/
│   ├── launch.json          # VS Code debug configuration
│   └── settings.json        # VS Code workspace settings
├── policies/
│   └── sample_ranger_policy.json  # Example Ranger policy file
├── ranger_to_lf_converter.py     # Conversion script
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## Prerequisites

* **Python 3.7+**
* **pip**
* **virtualenv** or **venv** (recommended)
* VS Code (optional, but recommended for debugging)

## Setup

1. **Clone or create** the project directory:

   ```bash
   git clone <your-repo-url> ranger-to-lf
   cd ranger-to-lf
   ```

2. **Create a virtual environment** and install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # macOS/Linux
   .venv\Scripts\activate       # Windows
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Verify** that dependencies are installed:

   ```bash
   pip list
   # You should see PyYAML among the installed packages
   ```

## Sample Ranger Policy

Located at `policies/sample_ranger_policy.json`:

```json
{
  "policies": [
    {
      "id": 101,
      "name": "sales_readwrite",
      "service": "hive_dev",
      "resourcePath": "/warehouse/sales.db/customers",
      "database": "sales",
      "table": "customers",
      "users": ["alice", "bob"],
      "groups": ["analysts"],
      "permissions": ["select", "insert", "update"]
    },
    {
      "id": 102,
      "name": "marketing_select",
      "service": "hive_dev",
      "resourcePath": "/warehouse/marketing.db/campaigns",
      "database": "marketing",
      "table": "campaigns",
      "users": [],
      "groups": ["marketing_team"],
      "permissions": ["select"]
    }
  ]
}
```

## Usage

### Command-line

To generate a CloudFormation YAML:

```bash
python ranger_to_lf_converter.py \
  --policies-dir policies \
  --output-dir output

```

* `--input`  : Path to your Ranger policy JSON file.
* `--output` : Desired path for the generated CFN template.


### Deploy

Run this to deploy:

```bash
for tmpl in output/*.yml; do
  name=$(basename "$tmpl" .yml)
  aws cloudformation deploy \
    --template-file "$tmpl" \
    --stack-name lf-permissions-"$name" \
    --capabilities CAPABILITY_NAMED_IAM
done


```


### VS Code Debug

1. Open the folder in VS Code.
2. Ensure the Python interpreter is set to `.venv` (should match `.vscode/settings.json`).
3. Press **F5** or select **Run → Start Debugging** to invoke the `Run converter` configuration.

## Output

After running, you’ll get `lakeformation_permissions.yml`, containing an `AWS::LakeFormation::Permissions` resource for each principal/table permission described in your Ranger policies.

### Example snippet from generated CFN

```yaml
Resources:
  LFPerm0_alice:
    Type: AWS::LakeFormation::Permissions
    Properties:
      DataLakePrincipal:
        DataLakePrincipalIdentifier: alice
      Resource:
        Table:
          CatalogId: !Ref AWS::AccountId
          DatabaseName: sales
          Name: customers
      Permissions:
        - SELECT
        - INSERT
        - ALTER
```

## Extending the Converter

* **Custom action mappings**: Edit the `ACTION_MAP` in `ranger_to_lf_converter.py`.
* **Resource types**: Add support for databases, columns, or S3 locations.
* **Principal resolution**: Integrate with IAM to resolve group ARNs.
* **Integration**: Embed this logic into a CDK or Terraform workflow.

## License

This code is provided under the MIT License. Feel free to adapt and extend.
