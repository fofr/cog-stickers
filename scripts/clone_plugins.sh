#!/bin/bash

# This script is used to clone specific versions of repositories.
# It takes a list of repositories and their commit hashes, clones them into a specific directory,
# and then checks out to the specified commit.

# List of repositories and their commit hashes to clone
# Each entry in the array is a string containing the repository URL and the commit hash separated by a space.
repos=(
  "https://github.com/huchenlei/ComfyUI-layerdiffuse 151f746"
)

# Destination directory
# This is where the repositories will be cloned into.
dest_dir="ComfyUI/custom_nodes/"

# Loop over each repository in the list
for repo in "${repos[@]}"; do
  # Extract the repository URL and the commit hash from the string
  repo_url=$(echo $repo | cut -d' ' -f1)
  commit_hash=$(echo $repo | cut -d' ' -f2)

  # Extract the repository name from the URL by removing the .git extension
  repo_name=$(basename "$repo_url" .git)

  # Check if the repository directory already exists
  if [ ! -d "$dest_dir$repo_name" ]; then
    # Clone the repository into the destination directory
    echo "Cloning $repo_url into $dest_dir$repo_name and checking out to commit $commit_hash"
    git clone --recursive "$repo_url" "$dest_dir$repo_name"

    # Use a subshell to avoid changing the main shell's working directory
    # Inside the subshell, change to the repository's directory and checkout to the specific commit
    (
      cd "$dest_dir$repo_name" && git checkout "$commit_hash"
      rm -rf .git

      # Recursively remove .git directories from submodules
      find . -type d -name ".git" -exec rm -rf {} +
    )
  else
    echo "Skipping clone for $repo_name, directory already exists"
  fi
done
