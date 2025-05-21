# Ranger to Lake Formation Converter

This project provides a Python utility that converts Apache Ranger policy JSON files in a directory into AWS Lake Formation CloudFormation templates. Each generated template defines corresponding Lake Formation permissions for tables in your data lake and can be deployed via the AWS CLI or AWS CloudFormation.

## Project Structure

```
ranger-to-lf/
├── .vscode/
│   ├── launch.json               # VS Code debug configuration
│   └── settings.json             # VS Code workspace settings
├── policies/                     # Directory of Ranger JSON policy files
│   ├── sample_ranger_policy.json # Example policies (multiple files supported)
│   └── ...                       # Additional JSON files per use case/domain
├── output/                       # Generated CloudFormation YAML files
│   └── *.yml                     # One CFN per input JSON
├── ranger_to_lf_converter.py     # Conversion script
├── requirements.txt              # Python dependencies
└── README.md                     # Project documentation
```

## Prerequisites

* **Python 3.7+**
* **pip**
* **venv** or **virtualenv** (recommended)
* **AWS CLI** configured with appropriate credentials
* VS Code (optional, but recommended)

## Setup

1. **Clone the repository**:

   ```bash
   git clone <your-repo-url> ranger-to-lf
   cd ranger-to-lf
   ```

2. **Create and activate a virtual environment**, then install dependencies:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate      # macOS/Linux
   .\.venv\Scripts\activate     # Windows
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Verify installation**:

   ```bash
   pip list | grep PyYAML
   ```

## Usage

### Convert Ranger policies to CFN

Run the converter to process all JSON files in `policies/` and write YAML templates into `output/`:

```bash
python ranger_to_lf_converter.py \
  --config config.yml \
  --policies-dir policies \
  --output-dir output

```

* `--policies-dir` (`-p`): Directory containing Ranger JSON policy files
* `--output-dir` (`-o`): Directory to write generated CloudFormation YAML files

### Deploy with AWS CLI

You can deploy each generated template as its own CloudFormation stack:

```bash
for tmpl in output/*.yml; do
  name=$(basename "$tmpl" .yml)
  aws cloudformation deploy \
    --template-file "$tmpl" \
    --stack-name lf-permissions-"$name" \
    --capabilities CAPABILITY_NAMED_IAM
done
```

**Tip**: Use a single merged template or nested stacks if you prefer one stack for all permissions.

### VS Code Debug Configuration

* Open the project folder in VS Code.
* Ensure the interpreter points to `.venv` (per `.vscode/settings.json`).
* Press **F5** or select **Run → Start Debugging** to run the `Run converter` launch configuration.

## Example Output Snippet

A section from `output/sample_ranger_policy.yml`:

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

* **Custom action mappings**: Modify `ACTION_MAP` in `ranger_to_lf_converter.py`.
* **Additional resource types**: Add support for databases, columns, or S3 locations.
* **Principal resolution**: Integrate with IAM to resolve ARNs for users/groups.
* **Infrastructure as Code**: Integrate within AWS CDK or Terraform workflows.

## License

.
