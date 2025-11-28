"""HomeAMP V2.0 - CLI entry point for agent."""

import logging
import sys

from homeamp_v2.agent.homeamp_agent import HomeAMPAgent
from homeamp_v2.core.config import get_settings
from homeamp_v2.core.logging import setup_logging

logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point for HomeAMP agent.

    Returns:
        Exit code (0 = success, 1 = error)
    """
    try:
        # Load settings
        settings = get_settings()

        # Setup logging
        setup_logging(
            log_level=settings.log_level,
            log_file=settings.log_file,
            log_format=settings.log_format,
        )

        logger.info("=" * 60)
        logger.info("HomeAMP Configuration Manager Agent")
        logger.info(f"Version: {settings.version}")
        logger.info(f"Environment: {settings.environment}")
        logger.info("=" * 60)

        # Create and start agent
        agent = HomeAMPAgent(settings)
        agent.start()

        return 0

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        return 0

    except Exception as e:
        logger.error(f"Agent failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
