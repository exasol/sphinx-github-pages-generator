declare -a StringArray=("../exasol_sphinx_github_pages_generator" )
sgpg --target_branch "github-pages/main"  \
  --push_origin "origin"  \
  --push_enabled "push"  \
  --source_branch "main"   \
  --module_path "${StringArray[@]}"
