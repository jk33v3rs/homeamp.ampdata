"""HomeAMP V2.0 - Data models package.

This package exports all SQLAlchemy models for the HomeAMP configuration manager.
"""

# Infrastructure models
from homeamp_v2.data.models.instance import Instance
from homeamp_v2.data.models.instance_group import InstanceGroup, InstanceGroupMember

# Tagging system
from homeamp_v2.data.models.tag import MetaTag, TagAssignment, TagRelationship

# Plugin models
from homeamp_v2.data.models.plugin import (
    Plugin,
    PluginMigration,
    PluginUpdateQueue,
    PluginUpdateSource,
    PluginVersion,
    InstancePlugin,
)

# Datapack models
from homeamp_v2.data.models.datapack import (
    Datapack,
    DatapackDeploymentQueue,
    DatapackUpdateSource,
    DatapackVersion,
    InstanceDatapack,
)

# Configuration models
from homeamp_v2.data.models.config import (
    ConfigChange,
    ConfigFileMetadata,
    ConfigRule,
    ConfigValue,
    ConfigVariable,
    ConfigVariance,
)

# Server properties
from homeamp_v2.data.models.server_property import ServerProperty, ServerPropertyVariance

# Deployment models
from homeamp_v2.data.models.deployment import (
    ApprovalRequest,
    ApprovalVote,
    DeploymentChange,
    DeploymentHistory,
    DeploymentLog,
    DeploymentQueue,
)

# World/Region/Rank models
from homeamp_v2.data.models.world import (
    PlayerRank,
    Rank,
    Region,
    RegionGroup,
    RegionGroupMember,
    World,
    WorldGroup,
    WorldGroupMember,
)

# Player models
from homeamp_v2.data.models.player import Player, PlayerConfigOverride, PlayerSession

# Monitoring models
from homeamp_v2.data.models.monitoring import (
    AgentHeartbeat,
    AuditLog,
    DiscoveryItem,
    DiscoveryRun,
    NotificationLog,
    ScheduledTask,
    SystemMetric,
    WebhookEvent,
)

# Advanced feature models
from homeamp_v2.data.models.advanced import APIKey, Backup, FeatureFlag

__all__ = [
    # Infrastructure
    "Instance",
    "InstanceGroup",
    "InstanceGroupMember",
    # Tagging
    "MetaTag",
    "TagAssignment",
    "TagRelationship",
    # Plugins
    "Plugin",
    "InstancePlugin",
    "PluginVersion",
    "PluginUpdateQueue",
    "PluginUpdateSource",
    "PluginMigration",
    # Datapacks
    "Datapack",
    "InstanceDatapack",
    "DatapackVersion",
    "DatapackDeploymentQueue",
    "DatapackUpdateSource",
    # Configuration
    "ConfigRule",
    "ConfigValue",
    "ConfigVariance",
    "ConfigChange",
    "ConfigVariable",
    "ConfigFileMetadata",
    # Server Properties
    "ServerProperty",
    "ServerPropertyVariance",
    # Deployment
    "DeploymentQueue",
    "DeploymentHistory",
    "DeploymentChange",
    "DeploymentLog",
    "ApprovalRequest",
    "ApprovalVote",
    # World/Region/Rank
    "World",
    "WorldGroup",
    "WorldGroupMember",
    "Region",
    "RegionGroup",
    "RegionGroupMember",
    "Rank",
    "PlayerRank",
    # Players
    "Player",
    "PlayerConfigOverride",
    "PlayerSession",
    # Monitoring
    "DiscoveryRun",
    "DiscoveryItem",
    "AgentHeartbeat",
    "SystemMetric",
    "AuditLog",
    "NotificationLog",
    "ScheduledTask",
    "WebhookEvent",
    # Advanced Features
    "FeatureFlag",
    "APIKey",
    "Backup",
]
