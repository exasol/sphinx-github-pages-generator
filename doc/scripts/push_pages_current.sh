declare -a StringArray=("../exasol_sphinx_github_pages_generator" )
sgpg --target_branch "github-pages/"$(git branch --show-current)""  \
  --push_origin "origin"  \
  --push_enabled "push"  \
  --module_path "${StringArray[@]}"
