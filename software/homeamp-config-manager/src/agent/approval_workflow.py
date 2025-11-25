"""
Multi-user Approval Workflow for ArchiveSMP Config Manager

Enhanced approval system with multiple reviewers and voting
"""

import mariadb
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import logging
from .notification_system import NotificationType, NotificationPriority

logger = logging.getLogger("approval_workflow")


class ApprovalWorkflow:
    """Manages multi-user approval requests"""

    def __init__(self, db_connection):
        """
        Initialize approval workflow

        Args:
            db_connection: MariaDB connection
        """
        self.db = db_connection
        self.cursor = db_connection.cursor(dictionary=True)

    def create_approval_request(
        self,
        change_type: str,
        change_description: str,
        change_data: Dict[str, Any],
        requested_by: str,
        required_approvals: int = 1,
        priority: str = "normal",
        auto_approve_after_hours: Optional[int] = None,
    ) -> int:
        """
        Create a new approval request

        Args:
            change_type: Type of change (plugin_update, config_change, deployment, etc.)
            change_description: Human-readable description
            change_data: Structured change data
            requested_by: Username requesting approval
            required_approvals: Number of approvals needed
            priority: normal, high, critical
            auto_approve_after_hours: Auto-approve if no response

        Returns:
            Request ID
        """
        query = """
            INSERT INTO change_approval_requests (
                change_type,
                change_description,
                change_data,
                requested_by,
                required_approvals,
                priority,
                auto_approve_after_hours,
                status,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending', NOW())
        """

        self.cursor.execute(
            query,
            (
                change_type,
                change_description,
                json.dumps(change_data),
                requested_by,
                required_approvals,
                priority,
                auto_approve_after_hours,
            ),
        )

        self.db.commit()
        request_id = self.cursor.lastrowid

        logger.info(f"Created approval request {request_id} by {requested_by}")

        # Create notification
        from .notification_system import create_notification_system

        notifier = create_notification_system(self.db)
        notifier.notify_approval_needed(
            change_type=change_type,
            change_description=change_description,
            requested_by=requested_by,
            approval_id=request_id,
        )

        return request_id

    def add_approval(self, request_id: int, approved_by: str, approved: bool, comment: str = "") -> Dict[str, Any]:
        """
        Add an approval vote

        Args:
            request_id: Approval request ID
            approved_by: Username voting
            approved: True for approve, False for reject
            comment: Optional comment

        Returns:
            Updated request status
        """
        # Record the vote
        query = """
            INSERT INTO approval_votes (
                request_id,
                voted_by,
                vote,
                comment,
                voted_at
            ) VALUES (%s, %s, %s, %s, NOW())
        """

        self.cursor.execute(query, (request_id, approved_by, "approved" if approved else "rejected", comment))

        self.db.commit()

        # Check if request should be auto-resolved
        return self._check_and_resolve(request_id)

    def _check_and_resolve(self, request_id: int) -> Dict[str, Any]:
        """
        Check if approval request can be resolved

        Args:
            request_id: Request to check

        Returns:
            Current status
        """
        # Get request details
        query = "SELECT * FROM change_approval_requests WHERE request_id = %s"
        self.cursor.execute(query, (request_id,))
        request = self.cursor.fetchone()

        if not request or request["status"] != "pending":
            return {"status": request["status"] if request else "not_found"}

        # Count votes
        query = """
            SELECT 
                COUNT(CASE WHEN vote = 'approved' THEN 1 END) as approvals,
                COUNT(CASE WHEN vote = 'rejected' THEN 1 END) as rejections
            FROM approval_votes
            WHERE request_id = %s
        """
        self.cursor.execute(query, (request_id,))
        votes = self.cursor.fetchone()

        new_status = None

        # Check if rejected
        if votes["rejections"] > 0:
            new_status = "rejected"

        # Check if approved
        elif votes["approvals"] >= request["required_approvals"]:
            new_status = "approved"

        # Check auto-approval timeout
        elif request["auto_approve_after_hours"]:
            query = """
                SELECT TIMESTAMPDIFF(HOUR, created_at, NOW()) as hours_elapsed
                FROM change_approval_requests
                WHERE request_id = %s
            """
            self.cursor.execute(query, (request_id,))
            elapsed = self.cursor.fetchone()

            if elapsed["hours_elapsed"] >= request["auto_approve_after_hours"]:
                new_status = "auto_approved"

        # Update status if changed
        if new_status:
            query = """
                UPDATE change_approval_requests
                SET status = %s,
                    resolved_at = NOW(),
                    approval_count = %s,
                    rejection_count = %s
                WHERE request_id = %s
            """

            self.cursor.execute(query, (new_status, votes["approvals"], votes["rejections"], request_id))

            self.db.commit()

            logger.info(f"Approval request {request_id} resolved: {new_status}")

            # Create notification
            from .notification_system import create_notification_system

            notifier = create_notification_system(self.db)

            if new_status in ["approved", "auto_approved"]:
                notifier.create_notification(
                    notification_type=NotificationType.APPROVAL_NEEDED,
                    title=f"Change approved: {request['change_type']}",
                    message=f"Approval request #{request_id} has been approved",
                    priority=NotificationPriority.MEDIUM,
                    related_entity_type="approval",
                    related_entity_id=str(request_id),
                )
            else:
                notifier.create_notification(
                    notification_type=NotificationType.APPROVAL_NEEDED,
                    title=f"Change rejected: {request['change_type']}",
                    message=f"Approval request #{request_id} has been rejected",
                    priority=NotificationPriority.HIGH,
                    related_entity_type="approval",
                    related_entity_id=str(request_id),
                )

        return {
            "status": new_status or "pending",
            "approvals": votes["approvals"],
            "rejections": votes["rejections"],
            "required_approvals": request["required_approvals"],
        }

    def get_pending_approvals(
        self, change_type: Optional[str] = None, priority: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get pending approval requests

        Args:
            change_type: Filter by change type
            priority: Filter by priority
            limit: Maximum results

        Returns:
            List of pending requests
        """
        query = "SELECT * FROM change_approval_requests WHERE status = 'pending'"
        params = []

        if change_type:
            query += " AND change_type = %s"
            params.append(change_type)

        if priority:
            query += " AND priority = %s"
            params.append(priority)

        query += " ORDER BY created_at DESC LIMIT %s"
        params.append(limit)

        self.cursor.execute(query, params)
        requests = self.cursor.fetchall()

        # Parse JSON data
        for req in requests:
            if req["change_data"]:
                req["change_data"] = json.loads(req["change_data"])

        return requests

    def get_request_votes(self, request_id: int) -> List[Dict[str, Any]]:
        """
        Get all votes for a request

        Args:
            request_id: Request ID

        Returns:
            List of votes
        """
        query = """
            SELECT * FROM approval_votes
            WHERE request_id = %s
            ORDER BY voted_at
        """

        self.cursor.execute(query, (request_id,))
        return self.cursor.fetchall()

    def can_user_vote(self, request_id: int, username: str) -> bool:
        """
        Check if user can vote on request

        Args:
            request_id: Request ID
            username: Username to check

        Returns:
            True if user can vote
        """
        # Get request
        query = "SELECT requested_by FROM change_approval_requests WHERE request_id = %s"
        self.cursor.execute(query, (request_id,))
        request = self.cursor.fetchone()

        if not request:
            return False

        # Can't vote on own request
        if request["requested_by"] == username:
            return False

        # Check if already voted
        query = "SELECT COUNT(*) as count FROM approval_votes WHERE request_id = %s AND voted_by = %s"
        self.cursor.execute(query, (request_id, username))
        result = self.cursor.fetchone()

        return result["count"] == 0

    def cancel_request(self, request_id: int, cancelled_by: str) -> bool:
        """
        Cancel a pending approval request

        Args:
            request_id: Request to cancel
            cancelled_by: Username cancelling

        Returns:
            Success status
        """
        query = """
            UPDATE change_approval_requests
            SET status = 'cancelled',
                resolved_at = NOW()
            WHERE request_id = %s
            AND status = 'pending'
            AND requested_by = %s
        """

        self.cursor.execute(query, (request_id, cancelled_by))
        self.db.commit()

        if self.cursor.rowcount > 0:
            logger.info(f"Approval request {request_id} cancelled by {cancelled_by}")
            return True

        return False


# Create votes table
CREATE_VOTES_TABLE = """
CREATE TABLE IF NOT EXISTS approval_votes (
    vote_id INT AUTO_INCREMENT PRIMARY KEY,
    request_id INT NOT NULL,
    voted_by VARCHAR(50) NOT NULL,
    vote ENUM('approved', 'rejected') NOT NULL,
    comment TEXT,
    voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (request_id) REFERENCES change_approval_requests(request_id) ON DELETE CASCADE,
    UNIQUE KEY unique_vote (request_id, voted_by),
    INDEX idx_request (request_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def create_approval_workflow(db_connection) -> ApprovalWorkflow:
    """Factory function to create approval workflow"""
    cursor = db_connection.cursor()
    cursor.execute(CREATE_VOTES_TABLE)
    db_connection.commit()
    cursor.close()

    return ApprovalWorkflow(db_connection)
