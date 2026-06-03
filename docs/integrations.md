# Integrations

gitsvg is a library and CLI first, but it also plugs into common toolchains so
you can keep diagram **source** under version control and render it where it's
needed — in CI, or directly inside your documentation.

## gitsvg-action — GitHub Action

[**gitsvg-action**](https://github.com/bertpl/gitsvg-action) renders, validates,
or drift-checks gitsvg diagrams in a GitHub Actions workflow. Keep your
`.gitsvg.jsonl` files in the repo and act on them in CI: render them to SVG,
validate them on every pull request, or fail the build when a committed SVG has
drifted out of sync with its source.

```yaml
steps:
  - uses: actions/checkout@v6
  - uses: bertpl/gitsvg-action@v1
    with:
      input: docs/diagrams      # a file or a directory tree
```

Three commands: `render` (default), `validate` (a cheap PR gate), and `check`
(fail when a committed `.svg` is stale relative to its source). No special
`permissions:` are needed — all three are read-only against your repository.

See the [gitsvg-action README](https://github.com/bertpl/gitsvg-action) for the
full input/output reference.

## mkdocs-gitsvg — MkDocs plugin

[**mkdocs-gitsvg**](https://github.com/bertpl/mkdocs-gitsvg) is a
[MkDocs](https://www.mkdocs.org/) plugin that renders gitsvg diagrams from
fenced code blocks to inline SVG at build time — so a git graph lives right in
your Markdown, with no checked-in image to keep in sync.

Enable the plugin in `mkdocs.yml`:

```yaml
plugins:
  - gitsvg
```

Then draw a graph in any page with a ` ```gitsvg ` fenced block whose body is a
gitsvg JSONL op-stream:

````markdown
```gitsvg
{"op": "branch", "name": "main", "label_side": "before"}
{"op": "commit", "branch": "main", "id": "c1", "msg": "initial commit", "hash": "auto"}
{"op": "commit", "branch": "main", "id": "c2", "msg": "add README", "hash": "auto"}
```
````

The block renders to an inline SVG git graph in the built site.

!!! note
    mkdocs-gitsvg is in active development and releasing soon — see the
    [project repository](https://github.com/bertpl/mkdocs-gitsvg) for current
    status and installation.
