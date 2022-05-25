declare -a StringArray=("../exasol_sphinx_github_pages_generator" )
python3 ./exasol_sphinx_github_pages_generator/deploy_github_pages.py \
  --target_branch "github-pages/main"  \
  --push_origin "origin"  \
  --push_enabled "push"  \
  --source_branch "main"   \
  --module_path "${StringArray[@]}"
