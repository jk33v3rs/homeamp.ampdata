"""HomeAMP V2.0 - Command Line Interface using Typer."""

import logging
from pathlib import Path
from typing import Optional

import typer
from homeamp_v2.core.config import get_settings
from homeamp_v2.core.logging import setup_logging
from homeamp_v2.data.unit_of_work import UnitOfWork
from homeamp_v2.domain.services import (
    BackupManager,
    ConfigService,
    DeploymentExecutor,
    DeploymentService,
    DeploymentValidator,
    DiscoveryService,
    UpdateService,
)
from rich.console import Console
from rich.table import Table

# Setup
setup_logging()
logger = logging.getLogger(__name__)
console = Console()
app = typer.Typer(help="HomeAMP Configuration Manager CLI")

# Sub-apps
instances_app = typer.Typer(help="Manage instances")
plugins_app = typer.Typer(help="Manage plugins")
deployments_app = typer.Typer(help="Manage deployments")
backups_app = typer.Typer(help="Manage backups")
configs_app = typer.Typer(help="Manage configurations")

app.add_typer(instances_app, name="instances")
app.add_typer(plugins_app, name="plugins")
app.add_typer(deployments_app, name="deployments")
app.add_typer(backups_app, name="backups")
app.add_typer(configs_app, name="configs")


# Instance commands
@instances_app.command("list")
def list_instances(
    platform: Optional[str] = typer.Option(None, help="Filter by platform"),
    active_only: bool = typer.Option(True, help="Show only active instances"),
):
    """List all instances."""
    uow = UnitOfWork()
    try:
        instances = uow.instances.get_all_instances(active_only=active_only)

        if platform:
            instances = [i for i in instances if i.platform == platform]

        table = Table(title="Instances")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Platform", style="blue")
        table.add_column("Version", style="yellow")
        table.add_column("Master", style="magenta")

        for instance in instances:
            table.add_row(
                str(instance.id),
                instance.name,
                instance.platform or "unknown",
                instance.minecraft_version or "unknown",
                "Yes" if instance.is_master else "No",
            )

        console.print(table)
        console.print(f"\n[green]Total: {len(instances)} instances[/green]")
    finally:
        uow.close()


@instances_app.command("scan")
def scan_instance(
    instance_id: int = typer.Argument(..., help="Instance ID to scan"),
):
    """Scan an instance for plugins, configs, etc."""
    uow = UnitOfWork()
    try:
        instance = uow.instances.get_by_id(instance_id)
        if not instance:
            console.print(f"[red]Instance {instance_id} not found[/red]")
            raise typer.Exit(1)

        console.print(f"[yellow]Scanning instance: {instance.name}[/yellow]")
        discovery = DiscoveryService(uow)
        discovery.scan_instance(instance_id)
        console.print(f"[green]Scan completed for {instance.name}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        uow.close()


@instances_app.command("scan-all")
def scan_all_instances():
    """Scan all active instances."""
    uow = UnitOfWork()
    try:
        console.print("[yellow]Scanning all instances...[/yellow]")
        discovery = DiscoveryService(uow)
        results = discovery.scan_all_instances()

        table = Table(title="Scan Results")
        table.add_column("Instance", style="cyan")
        table.add_column("Plugins", style="green")
        table.add_column("Configs", style="blue")
        table.add_column("Worlds", style="yellow")

        for result in results:
            table.add_row(
                result["instance_name"],
                str(result["plugins_found"]),
                str(result["configs_found"]),
                str(result["worlds_found"]),
            )

        console.print(table)
        console.print(f"[green]Scanned {len(results)} instances[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        uow.close()


# Plugin commands
@plugins_app.command("list")
def list_plugins(
    instance_id: Optional[int] = typer.Option(None, help="Filter by instance ID"),
    active_only: bool = typer.Option(True, help="Show only active plugins"),
):
    """List all plugins."""
    uow = UnitOfWork()
    try:
        if instance_id:
            plugins = uow.plugins.get_by_instance(instance_id)
        else:
            plugins = uow.session.query(uow.plugins.model).all()

        if active_only:
            plugins = [p for p in plugins if p.is_active]

        table = Table(title="Plugins")
        table.add_column("ID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("Version", style="yellow")
        table.add_column("Instance", style="blue")
        table.add_column("JAR File", style="magenta")

        for plugin in plugins:
            instance = uow.instances.get_by_id(plugin.instance_id)
            table.add_row(
                str(plugin.id),
                plugin.name,
                plugin.version or "unknown",
                instance.name if instance else "unknown",
                plugin.jar_filename,
            )

        console.print(table)
        console.print(f"[green]Total: {len(plugins)} plugins[/green]")
    finally:
        uow.close()


@plugins_app.command("check-updates")
def check_plugin_updates(
    instance_id: int = typer.Argument(..., help="Instance ID to check"),
):
    """Check for plugin updates."""
    uow = UnitOfWork()
    try:
        instance = uow.instances.get_by_id(instance_id)
        if not instance:
            console.print(f"[red]Instance {instance_id} not found[/red]")
            raise typer.Exit(1)

        console.print(f"[yellow]Checking updates for: {instance.name}[/yellow]")
        update_service = UpdateService(uow)
        updates = update_service.check_plugin_updates(instance_id)

        if not updates:
            console.print("[green]No updates available[/green]")
            return

        table = Table(title="Available Updates")
        table.add_column("Plugin", style="cyan")
        table.add_column("Current", style="yellow")
        table.add_column("Latest", style="green")
        table.add_column("Source", style="blue")

        for update in updates:
            table.add_row(
                update["plugin_name"],
                update["current_version"],
                update["latest_version"],
                update["source"],
            )

        console.print(table)
        console.print(f"[green]Found {len(updates)} updates[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        uow.close()


# Deployment commands
@deployments_app.command("list")
def list_deployments(
    instance_id: Optional[int] = typer.Option(None, help="Filter by instance ID"),
    status: Optional[str] = typer.Option(None, help="Filter by status"),
):
    """List deployments."""
    uow = UnitOfWork()
    try:
        if status == "pending":
            deployments = DeploymentService(uow).get_pending_deployments(instance_id)
        else:
            query = uow.session.query(uow.deployments.model)
            if instance_id:
                query = query.filter(uow.deployments.model.instance_id == instance_id)
            if status:
                query = query.filter(uow.deployments.model.status == status)
            deployments = query.all()

        table = Table(title="Deployments")
        table.add_column("ID", style="cyan")
        table.add_column("Instance", style="green")
        table.add_column("Type", style="blue")
        table.add_column("Target", style="yellow")
        table.add_column("Status", style="magenta")
        table.add_column("Priority", style="white")

        for deployment in deployments:
            instance = uow.instances.get_by_id(deployment.instance_id)
            table.add_row(
                str(deployment.id),
                instance.name if instance else "unknown",
                deployment.deployment_type,
                deployment.target_name or "unknown",
                deployment.status,
                str(deployment.priority or 5),
            )

        console.print(table)
        console.print(f"[green]Total: {len(deployments)} deployments[/green]")
    finally:
        uow.close()


@deployments_app.command("queue")
def queue_deployment(
    instance_id: int = typer.Argument(..., help="Instance ID"),
    deployment_type: str = typer.Argument(..., help="Deployment type (install/update/remove/config)"),
    target_name: str = typer.Argument(..., help="Target plugin/config name"),
    target_version: Optional[str] = typer.Option(None, help="Target version"),
    priority: int = typer.Option(5, help="Priority (1-10)"),
):
    """Queue a new deployment."""
    uow = UnitOfWork()
    try:
        instance = uow.instances.get_by_id(instance_id)
        if not instance:
            console.print(f"[red]Instance {instance_id} not found[/red]")
            raise typer.Exit(1)

        deployment_service = DeploymentService(uow)
        deployment_id = deployment_service.queue_deployment(
            instance_id=instance_id,
            deployment_type=deployment_type,
            target_name=target_name,
            target_version=target_version,
            priority=priority,
        )

        console.print(f"[green]Deployment {deployment_id} queued for {instance.name}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        uow.close()


@deployments_app.command("execute")
def execute_deployment(
    deployment_id: int = typer.Argument(..., help="Deployment ID to execute"),
):
    """Execute a deployment."""
    uow = UnitOfWork()
    try:
        deployment = uow.deployments.get_by_id(deployment_id)
        if not deployment:
            console.print(f"[red]Deployment {deployment_id} not found[/red]")
            raise typer.Exit(1)

        console.print(f"[yellow]Executing deployment {deployment_id}...[/yellow]")
        deployment_service = DeploymentService(uow)
        result = deployment_service.execute_deployment(deployment_id)

        if result.get("success"):
            console.print(f"[green]Deployment completed: {result.get('message')}[/green]")
        else:
            console.print(f"[red]Deployment failed: {result.get('message')}[/red]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        uow.close()


# Backup commands
@backups_app.command("create")
def create_backup(
    instance_id: int = typer.Argument(..., help="Instance ID to backup"),
    backup_type: str = typer.Option("full", help="Backup type (full/incremental/config_only)"),
    compression: str = typer.Option("gzip", help="Compression (gzip/bzip2/none)"),
):
    """Create a backup."""
    uow = UnitOfWork()
    try:
        instance = uow.instances.get_by_id(instance_id)
        if not instance:
            console.print(f"[red]Instance {instance_id} not found[/red]")
            raise typer.Exit(1)

        console.print(f"[yellow]Creating {backup_type} backup for {instance.name}...[/yellow]")
        backup_manager = BackupManager(uow)
        backup_path = backup_manager.create_backup(instance_id, backup_type, compression)

        console.print(f"[green]Backup created: {backup_path}[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        uow.close()


@backups_app.command("list")
def list_backups(
    instance_id: int = typer.Argument(..., help="Instance ID"),
):
    """List backups for an instance."""
    uow = UnitOfWork()
    try:
        instance = uow.instances.get_by_id(instance_id)
        if not instance:
            console.print(f"[red]Instance {instance_id} not found[/red]")
            raise typer.Exit(1)

        backup_manager = BackupManager(uow)
        backups = backup_manager.list_backups(instance_id)

        if not backups:
            console.print(f"[yellow]No backups found for {instance.name}[/yellow]")
            return

        table = Table(title=f"Backups for {instance.name}")
        table.add_column("Timestamp", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Size", style="yellow")
        table.add_column("Compression", style="blue")

        for backup in backups:
            table.add_row(
                backup["timestamp"],
                backup["type"],
                backup["size"],
                backup["compression"],
            )

        console.print(table)
        console.print(f"[green]Total: {len(backups)} backups[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        uow.close()


@backups_app.command("restore")
def restore_backup(
    instance_id: int = typer.Argument(..., help="Instance ID"),
    backup_path: str = typer.Argument(..., help="Path to backup file"),
):
    """Restore a backup."""
    uow = UnitOfWork()
    try:
        instance = uow.instances.get_by_id(instance_id)
        if not instance:
            console.print(f"[red]Instance {instance_id} not found[/red]")
            raise typer.Exit(1)

        console.print(f"[yellow]Restoring backup for {instance.name}...[/yellow]")
        backup_manager = BackupManager(uow)
        backup_manager.restore_backup(instance_id, Path(backup_path))

        console.print(f"[green]Backup restored successfully[/green]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        uow.close()


# Config commands
@configs_app.command("validate")
def validate_configs(
    instance_id: int = typer.Argument(..., help="Instance ID"),
):
    """Validate instance configurations."""
    uow = UnitOfWork()
    try:
        instance = uow.instances.get_by_id(instance_id)
        if not instance:
            console.print(f"[red]Instance {instance_id} not found[/red]")
            raise typer.Exit(1)

        console.print(f"[yellow]Validating configs for {instance.name}...[/yellow]")
        validator = DeploymentValidator(uow)
        result = validator.validate_pre_deployment(instance_id, "config")

        if result["passed"]:
            console.print("[green]All validations passed[/green]")
        else:
            console.print(f"[red]Validation failed: {result['critical_failures']} critical failures[/red]")

        table = Table(title="Validation Results")
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Message", style="yellow")

        for check in result["checks"]:
            status = "✓" if check["passed"] else "✗"
            status_color = "green" if check["passed"] else "red"
            table.add_row(
                check["check"],
                f"[{status_color}]{status}[/{status_color}]",
                check["message"],
            )

        console.print(table)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        uow.close()


@configs_app.command("detect-variances")
def detect_variances(
    instance_id: int = typer.Argument(..., help="Instance ID"),
):
    """Detect configuration variances."""
    uow = UnitOfWork()
    try:
        instance = uow.instances.get_by_id(instance_id)
        if not instance:
            console.print(f"[red]Instance {instance_id} not found[/red]")
            raise typer.Exit(1)

        console.print(f"[yellow]Detecting variances for {instance.name}...[/yellow]")
        config_service = ConfigService(uow)
        variances = config_service.detect_variances(instance_id)

        if not variances:
            console.print("[green]No variances detected[/green]")
            return

        table = Table(title="Configuration Variances")
        table.add_column("Plugin", style="cyan")
        table.add_column("Key", style="green")
        table.add_column("Current", style="yellow")
        table.add_column("Expected", style="blue")

        for variance in variances:
            table.add_row(
                variance["plugin_name"],
                variance["config_key"],
                str(variance["current_value"]),
                str(variance["expected_value"]),
            )

        console.print(table)
        console.print(f"[yellow]Found {len(variances)} variances[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)
    finally:
        uow.close()


if __name__ == "__main__":
    app()
