
## Development

### Initial Setup

```bash
make
```

### Commands

After this the command `inv` is used:

```bash
inv --list
inv install        # install updates
inv check          # run all quality checks
inv docker.build   # build a docker image
```

For some scripts a `GITHUB_TOKEN` is required:

```bash
# for example with infisical
# source everthing
source <(infisical export --path /github)
# or only set  the token
export GITHUB_TOKEN=$(infisical secrets get --path /github GITHUB_TOKEN --plain)
```

### Release

For a release run `inv release`.
Merge this change into the `main` branch and tag it accordingly
and if needed create a GitHub release.

## Todos

- [x] Only upload images from the same stack
- [x] At the moment the `restore` function is not implemented yet -> generates bash script
- [ ] Upload files into the "cloud"
