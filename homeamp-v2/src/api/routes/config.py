"""HomeAMP V2.0 - Configuration management API routes."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from homeamp_v2.api.dependencies import get_uow
from homeamp_v2.core.exceptions import ConfigNotFoundError, ValidationError
from homeamp_v2.data.unit_of_work import UnitOfWork
from homeamp_v2.domain.services.config_service import ConfigService
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["config"])


class GlobalConfigRuleRequest(BaseModel):
    """Schema for creating global config rule."""

    plugin_name: str = Field(..., min_length=1, max_length=255)
    file_path: str = Field(..., min_length=1, max_length=500)
    key_path: str = Field(..., min_length=1, max_length=500)
    expected_value: str
    enforcement_level: str = Field(
        default="recommended", pattern="^(required|recommended|optional)$"
    )
    description: Optional[str] = Field(None, max_length=1000)


class ConfigRuleResponse(BaseModel):
    """Schema for config rule response."""

    id: int
    plugin_name: str
    file_path: str
    key_path: str
    expected_value: str
    scope_type: str
    enforcement_level: str
    description: Optional[str]


class ConfigResolutionResponse(BaseModel):
    """Schema for config resolution response."""

    instance_id: int
    plugin_name: str
    key_path: str
    resolved_value: Optional[str]
    rule_source: Optional[str]
    total_matching_rules: int


class ConfigVariableRequest(BaseModel):
    """Schema for creating config variable."""

    name: str = Field(..., min_length=1, max_length=100)
    value: str
    scope_type: str = Field(default="global", pattern="^(global|instance|group)$")
    scope_id: Optional[int] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=1000)


class ConfigVariableResponse(BaseModel):
    """Schema for config variable response."""

    id: int
    name: str
    value: str
    scope_type: str
    scope_id: Optional[int]
    description: Optional[str]
    created_at: str
    updated_at: str


@router.get("/global", response_model=List[ConfigRuleResponse])
def list_global_config_rules(
    plugin_name: Optional[str] = Query(None, description="Filter by plugin name"),
    uow: UnitOfWork = Depends(get_uow),
):
    """List all global configuration rules.

    Args:
        plugin_name: Optional plugin name filter
        uow: Unit of Work

    Returns:
        List of global config rules
    """
    try:
        with uow:
            config_service = ConfigService(uow)
            rules = config_service.get_global_config_rules(plugin_name=plugin_name)

        return [
            ConfigRuleResponse(
                id=rule["id"],
                plugin_name=rule["plugin_name"],
                file_path=rule["file_path"],
                key_path=rule["key_path"],
                expected_value=rule["expected_value"],
                scope_type="global",
                enforcement_level=rule["enforcement_level"],
                description=rule.get("description"),
            )
            for rule in rules
        ]
    except Exception as e:
        logger.error(f"Error listing global config rules: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/global", response_model=ConfigRuleResponse, status_code=201)
def create_global_config_rule(
    request: GlobalConfigRuleRequest, uow: UnitOfWork = Depends(get_uow)
):
    """Create a new global configuration rule.

    Args:
        request: Config rule creation request
        uow: Unit of Work

    Returns:
        Created config rule
    """
    try:
        with uow:
            config_service = ConfigService(uow)
            rule = config_service.create_global_config_rule(
                plugin_name=request.plugin_name,
                file_path=request.file_path,
                key_path=request.key_path,
                expected_value=request.expected_value,
                enforcement_level=request.enforcement_level,
                description=request.description,
            )

        return ConfigRuleResponse(
            id=rule["id"],
            plugin_name=rule["plugin_name"],
            file_path=rule["file_path"],
            key_path=rule["key_path"],
            expected_value=rule["expected_value"],
            scope_type=rule["scope_type"],
            enforcement_level=rule["enforcement_level"],
            description=request.description,
        )
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating global config rule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resolve", response_model=ConfigResolutionResponse)
def resolve_config(
    instance_id: int = Query(..., gt=0),
    plugin_name: str = Query(..., min_length=1),
    key_path: str = Query(..., min_length=1),
    uow: UnitOfWork = Depends(get_uow),
):
    """Resolve final config value for an instance.

    Considers both global and instance-specific rules.
    Instance-specific rules override global rules.

    Args:
        instance_id: Instance ID
        plugin_name: Plugin name
        key_path: Config key path
        uow: Unit of Work

    Returns:
        Config resolution result
    """
    try:
        with uow:
            config_service = ConfigService(uow)
            result = config_service.resolve_config_for_instance(
                instance_id=instance_id, plugin_name=plugin_name, key_path=key_path
            )

        return ConfigResolutionResponse(
            instance_id=result["instance_id"],
            plugin_name=result["plugin_name"],
            key_path=result["key_path"],
            resolved_value=result["resolved_value"],
            rule_source=result["rule_source"],
            total_matching_rules=result["total_matching_rules"],
        )
    except ConfigNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error resolving config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/variances")
def list_variances(
    instance_id: Optional[int] = Query(None, gt=0),
    severity: Optional[int] = Query(None, ge=0, le=10),
    uow: UnitOfWork = Depends(get_uow),
):
    """List configuration variances (drift).

    Args:
        instance_id: Optional instance ID filter
        severity: Optional severity level filter
        uow: Unit of Work

    Returns:
        List of variances
    """
    try:
        with uow:
            variances = uow.configs.get_variances(
                instance_id=instance_id, severity=severity
            )

        return {
            "variances": [
                {
                    "id": v.id,
                    "instance_id": v.instance_id,
                    "rule_id": v.rule_id,
                    "expected_value": v.expected_value,
                    "actual_value": v.actual_value,
                    "severity": v.severity,
                    "status": v.status,
                    "auto_resolvable": v.auto_resolvable,
                    "detected_at": v.detected_at.isoformat() if v.detected_at else None,
                }
                for v in variances
            ],
            "total": len(variances),
        }
    except Exception as e:
        logger.error(f"Error listing variances: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/variances/{instance_id}/detect")
def detect_variances(instance_id: int, uow: UnitOfWork = Depends(get_uow)):
    """Detect configuration variances for an instance.

    Args:
        instance_id: Instance ID
        uow: Unit of Work

    Returns:
        Detected variances
    """
    try:
        with uow:
            config_service = ConfigService(uow)
            variances = config_service.detect_variances(instance_id)

        return {"instance_id": instance_id, "variances": variances, "total": len(variances)}
    except ConfigNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error detecting variances for instance {instance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/enforce/{instance_id}")
def enforce_config_rules(
    instance_id: int,
    dry_run: bool = Query(True, description="Simulate changes without applying"),
    uow: UnitOfWork = Depends(get_uow),
):
    """Enforce configuration rules on an instance.

    Args:
        instance_id: Instance ID
        dry_run: If true, simulate changes without applying
        uow: Unit of Work

    Returns:
        Enforcement results
    """
    try:
        with uow:
            config_service = ConfigService(uow)
            result = config_service.enforce_config_rules(
                instance_id=instance_id, dry_run=dry_run
            )

        return result
    except ConfigNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error enforcing config rules for instance {instance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/variables", response_model=ConfigVariableResponse, status_code=201)
def create_config_variable(
    request: ConfigVariableRequest, uow: UnitOfWork = Depends(get_uow)
):
    """Create a configuration variable.

    Args:
        request: Config variable request
        uow: Unit of Work

    Returns:
        Created config variable
    """
    try:
        from homeamp_v2.data.models.config import ConfigVariable

        with uow:
            variable = ConfigVariable(
                name=request.name,
                value=request.value,
                scope_type=request.scope_type,
                scope_id=request.scope_id,
                description=request.description,
            )
            uow.session.add(variable)
            uow.commit()

        return ConfigVariableResponse(
            id=variable.id,
            name=variable.name,
            value=variable.value,
            scope_type=variable.scope_type,
            scope_id=variable.scope_id,
            description=variable.description,
            created_at=variable.created_at.isoformat() if variable.created_at else "",
            updated_at=variable.updated_at.isoformat() if variable.updated_at else "",
        )
    except Exception as e:
        logger.error(f"Error creating config variable: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/variables", response_model=List[ConfigVariableResponse])
def list_config_variables(
    scope_type: Optional[str] = Query(None, pattern="^(global|instance|group)$"),
    scope_id: Optional[int] = Query(None, gt=0),
    uow: UnitOfWork = Depends(get_uow),
):
    """List configuration variables.

    Args:
        scope_type: Optional scope type filter
        scope_id: Optional scope ID filter
        uow: Unit of Work

    Returns:
        List of config variables
    """
    try:
        from homeamp_v2.data.models.config import ConfigVariable
        from sqlalchemy import select

        with uow:
            stmt = select(ConfigVariable)

            if scope_type:
                stmt = stmt.where(ConfigVariable.scope_type == scope_type)

            if scope_id is not None:
                stmt = stmt.where(ConfigVariable.scope_id == scope_id)

            result = uow.session.execute(stmt)
            variables = result.scalars().all()

        return [
            ConfigVariableResponse(
                id=v.id,
                name=v.name,
                value=v.value,
                scope_type=v.scope_type,
                scope_id=v.scope_id,
                description=v.description,
                created_at=v.created_at.isoformat() if v.created_at else "",
                updated_at=v.updated_at.isoformat() if v.updated_at else "",
            )
            for v in variables
        ]
    except Exception as e:
        logger.error(f"Error listing config variables: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hierarchy/{plugin_name}")
def get_config_hierarchy(plugin_name: str, uow: UnitOfWork = Depends(get_uow)):
    """Get configuration hierarchy for a plugin.

    Args:
        plugin_name: Plugin name
        uow: Unit of Work

    Returns:
        Configuration hierarchy
    """
    try:
        with uow:
            config_service = ConfigService(uow)
            hierarchy = config_service.get_config_hierarchy(plugin_name)

        return hierarchy
    except Exception as e:
        logger.error(f"Error getting config hierarchy for {plugin_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
