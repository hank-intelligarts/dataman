import json
import os
import subprocess
from pathlib import Path

import click
import git

from dataman.metadata import read_metadata
from dataman.naming import validate_name, validate_version
from dataman.scanner import scan_dataset


@click.group()
def cli():
    """dataman — AI training dataset management."""


@cli.group("config")
def config_group():
    """Manage dataman configuration."""


@config_group.command("init")
def config_init():
    """Interactive wizard to create ~/.dataman/config.toml."""
    config_dir = Path.home() / ".dataman"
    config_path = config_dir / "config.toml"
    config_dir.mkdir(exist_ok=True)

    click.echo("dataman config init — set up NFS remotes for this machine.\n")

    remotes = {}
    routing = {}

    while True:
        remote_name = click.prompt("NFS remote name (e.g. nfs-1)", default="").strip()
        if not remote_name:
            break
        mount_path = click.prompt(f"Mount path for {remote_name} (e.g. /mnt/nfs1/dvc-remote)").strip()
        remotes[remote_name] = mount_path
        more = click.confirm("Add another NFS remote?", default=False)
        if not more:
            break

    if not remotes:
        raise click.ClickException("At least one NFS remote is required.")

    default_remote = click.prompt(
        "Default NFS remote (used when dataset has no routing rule)",
        default=list(remotes.keys())[0],
    )

    click.echo("\nDataset routing (map dataset names to NFS remotes).")
    click.echo("Press Enter with empty name to finish.\n")
    while True:
        ds_name = click.prompt("Dataset name", default="").strip()
        if not ds_name:
            break
        ds_remote = click.prompt(f"NFS remote for '{ds_name}'", default=default_remote)
        routing[ds_name] = ds_remote

    lines = ["[nfs]", f'default = "{default_remote}"', "", "[nfs.remotes]"]
    for name, path in remotes.items():
        lines.append(f'{name} = "{path}"')
    if routing:
        lines.append("")
        lines.append("[nfs.routing]")
        for ds, remote in routing.items():
            lines.append(f'{ds} = "{remote}"')
    lines.append("")

    config_path.write_text("\n".join(lines))
    click.echo(f"\nConfig written to {config_path}")


@cli.command()
@click.option("--path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--name", required=True)
@click.option("--version", required=True)
@click.option("--registered-by", default=lambda: os.environ.get("USER", "unknown"))
@click.option("--repo-path", default=".", type=click.Path(path_type=Path))
def register(path, name, version, registered_by, repo_path):
    """Register a dataset: scan, write metadata, DVC add+push, Git tag+push."""
    try:
        validate_name(name)
        validate_version(version)
    except ValueError as e:
        raise click.ClickException(str(e))

    from dataman.nfs_config import load_nfs_config, resolve_remote
    try:
        nfs_cfg = load_nfs_config()
        nfs_remote = resolve_remote(name, nfs_cfg)
    except (FileNotFoundError, ValueError) as e:
        raise click.ClickException(str(e))

    from dataman.registry import register_dataset
    result = register_dataset(
        path=path,
        name=name,
        version=version,
        registered_by=registered_by,
        repo_path=repo_path,
        nfs_remote=nfs_remote,
    )
    click.echo(f"Registered: {result.snapshot_id}")
    click.echo(f"NFS remote: {nfs_remote}")
    click.echo(f"Files: {result.file_count}  Quality: {result.quality_score}%  Issues: {result.issue_count}")


@cli.command()
@click.option("--path", required=True, type=click.Path(exists=True, path_type=Path))
def info(path):
    """Show metadata for a registered dataset directory."""
    meta = read_metadata(path)
    click.echo(json.dumps(meta, indent=2))


@cli.command("list")
@click.option("--repo-path", default=".", type=click.Path(path_type=Path))
def list_datasets(repo_path):
    """List all registered dataset snapshot IDs from Git tags."""
    from dataman.git_ops import get_all_tags
    tags = get_all_tags(repo_path)
    if not tags:
        click.echo("No datasets registered yet.")
        return
    for tag in sorted(tags):
        click.echo(tag)


@cli.command()
@click.option("--path", required=True, type=click.Path(exists=True, path_type=Path))
def scan(path):
    """Run quality checks on a dataset directory and print results."""
    result = scan_dataset(path)
    click.echo(f"file_count: {result.file_count}")
    click.echo(f"total_size_bytes: {result.total_size_bytes}")
    click.echo(f"quality_score: {result.quality_score}%")
    if result.issues:
        click.echo(f"issues ({len(result.issues)}):")
        for issue in result.issues:
            click.echo(f"  [{issue.kind}] {issue.file} — {issue.detail}")
    else:
        click.echo("No issues found.")


@cli.command()
@click.option("--path", required=True, type=click.Path(exists=True, path_type=Path))
def verify(path):
    """Verify a registered dataset: re-scan and compare to stored metadata."""
    meta = read_metadata(path)
    result = scan_dataset(path)
    stored_score = meta.get("quality_score", -1)
    stored_count = meta.get("file_count", -1)

    ok = True
    if result.file_count != stored_count:
        click.echo(f"FAIL file_count: stored={stored_count} current={result.file_count}")
        ok = False
    if abs(result.quality_score - stored_score) > 0.01:
        click.echo(f"FAIL quality_score: stored={stored_score} current={result.quality_score}")
        ok = False
    if ok:
        click.echo("OK — dataset matches stored metadata.")
    else:
        raise SystemExit(1)


@cli.command()
@click.argument("snapshot_id")
@click.option("--repo-path", default=".", type=click.Path(path_type=Path))
def pull(snapshot_id, repo_path):
    """Checkout a snapshot tag and pull its data via DVC."""
    try:
        repo = git.Repo(repo_path)
        repo.git.checkout(snapshot_id)
    except git.GitCommandError as e:
        raise click.ClickException(f"git checkout failed: {e}")

    # Resolve NFS remote from snapshot_id (e.g. "dataset/pedestrian/v2.0" → "pedestrian")
    parts = snapshot_id.split("/")
    if len(parts) != 3:
        raise click.ClickException(f"Invalid snapshot_id format: {snapshot_id!r}. Expected dataset/name/vX.Y")
    dataset_name = parts[1]

    from dataman.nfs_config import load_nfs_config, resolve_remote
    try:
        nfs_cfg = load_nfs_config()
        nfs_remote = resolve_remote(dataset_name, nfs_cfg)
    except (FileNotFoundError, ValueError) as e:
        raise click.ClickException(str(e))

    result = subprocess.run(
        ["dvc", "pull", "-r", nfs_remote],
        capture_output=True, text=True, cwd=str(repo_path)
    )
    if result.returncode != 0:
        raise click.ClickException(f"dvc pull failed: {result.stderr.strip()}")
    click.echo(f"Data for {snapshot_id} pulled successfully (remote: {nfs_remote}).")


@cli.command()
@click.option("--repo-path", default=".", type=click.Path(path_type=Path))
@click.option("--host", default="0.0.0.0")
@click.option("--port", default=8000, type=int)
def serve(repo_path, host, port):
    """Start the dataman web UI server."""
    from dataman.nfs_config import load_nfs_config, get_all_dataset_paths
    try:
        nfs_cfg = load_nfs_config()
        nfs_dataset_paths = get_all_dataset_paths(nfs_cfg)
    except FileNotFoundError as e:
        raise click.ClickException(str(e))

    import uvicorn
    from dataman.web.app import create_app
    app = create_app(repo_path=repo_path, nfs_dataset_paths=nfs_dataset_paths)
    uvicorn.run(app, host=host, port=port)
