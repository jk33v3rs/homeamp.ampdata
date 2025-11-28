"""HomeAMP V2.0 - Custom exception classes."""


class HomeAMPException(Exception):
    """Base exception for all HomeAMP errors."""

    pass


class DatabaseError(HomeAMPException):
    """Database operation failed."""

    pass


class ValidationError(HomeAMPException):
    """Data validation failed."""

    pass


class InstanceNotFoundError(HomeAMPException):
    """Instance not found in database."""

    pass


class PluginNotFoundError(HomeAMPException):
    """Plugin not found in database."""

    pass


class ConfigNotFoundError(HomeAMPException):
    """Config rule or value not found."""

    pass


class DeploymentError(HomeAMPException):
    """Deployment execution failed."""

    pass


class BackupError(HomeAMPException):
    """Backup creation or restoration failed."""

    pass


class DiscoveryError(HomeAMPException):
    """Discovery process failed."""

    pass


class UpdateCheckError(HomeAMPException):
    """Update checking failed."""

    pass


class AuthenticationError(HomeAMPException):
    """Authentication or authorization failed."""

    pass


class IntegrationError(HomeAMPException):
    """External integration failed."""

    pass


class AgentError(HomeAMPException):
    """Agent operation failed."""

    pass


class NotFoundError(HomeAMPException):
    """Resource not found."""

    pass


class ApprovalError(HomeAMPException):
    """Approval workflow error."""

    pass
