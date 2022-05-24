declare -a StringArray=("../exasol_sphinx_github_pages_generator" )
python3 ./exasol_sphinx_github_pages_generator/deploy_github_pages.py  \
  --target_branch "github-pages/"$(git branch --show-current)""  \
  --push_origin "origin"  \
  --push_enabled "push"  \
  --module_path "${StringArray[@]}"
