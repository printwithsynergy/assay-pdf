# Getting help

Thanks for using AssayPDF. Before opening an issue, please check the
docs — most setup and runtime questions are answered there.

## Self-serve

| Question | Where to look |
|---|---|
| How do I install it? | [docs/install.md](docs/install.md) |
| How do I run an end-to-end benchmark? | [docs/usage.md](docs/usage.md) |
| What does flag `--foo` do? | [docs/cli.md](docs/cli.md) |
| Something errored — is this known? | [docs/troubleshooting.md](docs/troubleshooting.md), [docs/known-quirks.md](docs/known-quirks.md) |
| How do I reproduce a published score? | [docs/reproducing.md](docs/reproducing.md) |
| How does the scoring methodology work? | [docs/methodology.md](docs/methodology.md) |
| Why is the architecture set up this way? | [docs/architecture.md](docs/architecture.md), [docs/adr/](docs/adr/) |

## Asking a question

If the docs don't answer it, open a
[GitHub Discussion](https://github.com/thinkneverland/assay-pdf/discussions)
in the **Q&A** category. Include:

- What you're trying to do.
- What you ran (exact command).
- What happened vs. what you expected.
- AssayPDF version (`uv run assay --version`), Python version, OS, and
  the version of any preflight engine involved.

## Reporting a bug

Open a [bug report](https://github.com/thinkneverland/assay-pdf/issues/new?template=bug.md).
The template asks for the information needed to triage quickly.

## Proposing new rule coverage or an engine runner

Use the
[New rule coverage](https://github.com/thinkneverland/assay-pdf/issues/new?template=new-rule-coverage.md)
template, or open a feature request describing the engine you want to
benchmark. See [CONTRIBUTING.md](CONTRIBUTING.md) for the implementation
shape.

## Reporting a security issue

**Do not open a public issue.** See [SECURITY.md](SECURITY.md) for the
private reporting channel.

## Commercial support

AssayPDF is maintained by Think Neverland alongside
[lintPDF](https://github.com/thinkneverland) (PDF preflight SaaS, in
private development). For commercial integration questions, email
**iam@quincy.codes**.
