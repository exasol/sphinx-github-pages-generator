declare -a StringArray=("../exasol_sphinx_github_pages_generator" )
sgpg --target_branch "github-pages/main" \
  --push_origin "origin" \
  --push_enabled "push" \
  --module_path "${StringArray[@]}" \
  --source_branch "$(git tag --sort=committerdate | tail -1)" \
  --source_origin "tags"

