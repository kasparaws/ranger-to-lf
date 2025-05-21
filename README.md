# ranger-to-lf Converter

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
├── config.yml                    # Configuration file for overrides
└── README.md                     # Project documentation
```

## Prerequisites

* **Python 3.7+**
* **pip**
* **venv** or **virtualenv** (recommended)
* **AWS CLI** configured with appropriate credentials
* VS Code (optional)

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
   .\.venv\Scripts\activate    # Windows
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Verify installation**:

   ```bash
   pip list | grep PyYAML
   ```

## Configuration

The converter uses a `config.yml` file to control account, principal ARNs, and overrides:

```yaml
# AWS account ID for Lake Formation CatalogId
account_id: "111111111"

# ARN template for principals; use {account} and {principal}
principal_arn_template: "arn:aws:iam::{account}:role/{principal}"

# Default database if not specified in policy JSON
default_database: "default_db"

# Override mappings for database, table, and groups
database_overrides:
  sales: "sales_prod"
  marketing: "marketing_prod"

table_overrides:
  pricing_models: "pricing_models_prod"
  reimbursement:    "reimbursement_prod"

group_overrides:
  analysts:            "Admin"
  market_access_team:  "MarketAccessAdminRole"
  ma_lead:             "MarketAccessLeadRole"
  brand_mgr:           "BrandAdminRole"
```

* **`database_overrides`**: map source DB names to target DB names.
* **`table_overrides`**: map source table names to target table names.
* **`group_overrides`**: map Ranger groups to IAM role names before ARN construction.

## Usage

### Convert Ranger policies to CFN

```bash
python ranger_to_lf_converter.py \
  --config config.yml \
  --policies-dir policies \
  --output-dir output
```

* `--config` (`-c`): Path to your `config.yml` file.
* `--policies-dir` (`-p`): Directory containing Ranger JSON policy files.
* `--output-dir` (`-o`): Directory to write generated CloudFormation YAML files.

### Deploy with AWS CLI

```bash
for tmpl in output/*.yml; do
  name=$(basename "$tmpl" .yml)
  aws cloudformation deploy \
    --template-file "$tmpl" \
    --stack-name lf-permissions-"$name" \
    --capabilities CAPABILITY_NAMED_IAM
  echo "Deployed stack: lf-permissions-$name"
done
```

## VS Code Debug Configuration

* Open the project folder in VS Code.
* Ensure the interpreter points to `.venv` (per `.vscode/settings.json`).
* Press **F5** or select **Run → Start Debugging** to run the converter.

## Extending the Converter

* **Custom action mappings**: Modify `ACTION_MAP` in `ranger_to_lf_converter.py`.
* **Additional resource types**: Add support for databases, columns, or S3 locations.
* **Principal resolution**: Integrate with IAM to resolve ARNs dynamically.
* **Infrastructure as Code**: Integrate within AWS CDK or Terraform workflows.

## License

 
