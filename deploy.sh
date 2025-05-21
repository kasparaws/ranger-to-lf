for tmpl in output/*.yml; do
  name=$(basename "$tmpl" .yml)
  aws cloudformation deploy \
    --template-file "$tmpl" \
    --stack-name lf-permissions-"$name" \
    --capabilities CAPABILITY_NAMED_IAM
done
