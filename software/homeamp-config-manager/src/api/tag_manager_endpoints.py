"""
Tag Manager API Endpoints
Manage meta-tags, categories, and instance assignments
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import mysql.connector
import json
import os

router = APIRouter(prefix="/api/tags", tags=["Tag Manager"])

# Database connection helper
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "asmp_admin"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "asmp_config")
    )

# ==================== Models ====================

class TagCategory(BaseModel):
    category_id: Optional[int] = None
    category_name: str
    display_name: str
    description: Optional[str] = None
    is_multiselect: bool = True
    is_required: bool = False
    display_order: int = 999
    icon: Optional[str] = None
    color: Optional[str] = None

class MetaTag(BaseModel):
    tag_id: Optional[int] = None
    category_id: int
    tag_name: str
    display_name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_system_tag: bool = False
    is_deprecated: bool = False
    replacement_tag_id: Optional[int] = None
    metadata_json: Optional[str] = None
    category_name: Optional[str] = None  # For display
    category_display_name: Optional[str] = None

class InstanceTagAssignment(BaseModel):
    instance_id: str
    tag_id: int
    applied_by: str = "web_ui"
    is_auto_detected: bool = False
    confidence_score: Optional[float] = None

class TagAssignmentBulk(BaseModel):
    instance_ids: List[str]
    tag_id: int
    applied_by: str = "web_ui"

class TagDependency(BaseModel):
    dependency_id: Optional[int] = None
    dependent_tag_id: int
    required_tag_id: int
    dependency_type: str = "required"  # required, recommended, optional
    description: Optional[str] = None

class TagConflict(BaseModel):
    conflict_id: Optional[int] = None
    tag_a_id: int
    tag_b_id: int
    conflict_severity: str = "error"  # error, warning, info
    description: Optional[str] = None

# ==================== Endpoints ====================

@router.get("/categories", response_model=List[TagCategory])
async def get_tag_categories():
    """Get all tag categories"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT category_id, category_name, display_name, description,
                   is_multiselect, is_required, display_order, icon, color
            FROM meta_tag_categories
            ORDER BY display_order ASC, category_name ASC
        """)
        categories = cursor.fetchall()
        return categories
    finally:
        cursor.close()
        conn.close()

@router.post("/categories")
async def create_tag_category(category: TagCategory):
    """Create a new tag category"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO meta_tag_categories 
            (category_name, display_name, description, is_multiselect, is_required, display_order, icon, color)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            category.category_name, category.display_name, category.description,
            category.is_multiselect, category.is_required, category.display_order,
            category.icon, category.color
        ))
        conn.commit()
        return {"category_id": cursor.lastrowid, "message": "Category created"}
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=400, detail="Category name already exists")
    finally:
        cursor.close()
        conn.close()

@router.put("/categories/{category_id}")
async def update_tag_category(category_id: int, category: TagCategory):
    """Update a tag category"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE meta_tag_categories
            SET display_name=%s, description=%s, is_multiselect=%s, is_required=%s,
                display_order=%s, icon=%s, color=%s
            WHERE category_id=%s
        """, (
            category.display_name, category.description, category.is_multiselect,
            category.is_required, category.display_order, category.icon,
            category.color, category_id
        ))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Category not found")
            
        return {"message": "Category updated"}
    finally:
        cursor.close()
        conn.close()

@router.delete("/categories/{category_id}")
async def delete_tag_category(category_id: int):
    """Delete a tag category (only if no tags exist)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check if category has tags
        cursor.execute("SELECT COUNT(*) as count FROM meta_tags WHERE category_id=%s", (category_id,))
        result = cursor.fetchone()
        if result[0] > 0:
            raise HTTPException(status_code=400, detail="Cannot delete category with tags")
        
        cursor.execute("DELETE FROM meta_tag_categories WHERE category_id=%s", (category_id,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Category not found")
            
        return {"message": "Category deleted"}
    finally:
        cursor.close()
        conn.close()

@router.get("/all", response_model=List[MetaTag])
async def get_all_tags():
    """Get all meta-tags with category info"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT t.tag_id, t.category_id, t.tag_name, t.display_name, t.description,
                   t.icon, t.color, t.is_system_tag, t.is_deprecated, t.replacement_tag_id,
                   t.metadata_json, c.category_name, c.display_name as category_display_name
            FROM meta_tags t
            JOIN meta_tag_categories c ON t.category_id = c.category_id
            WHERE t.is_deprecated = FALSE
            ORDER BY c.display_order ASC, t.display_name ASC
        """)
        tags = cursor.fetchall()
        return tags
    finally:
        cursor.close()
        conn.close()

@router.post("/create")
async def create_tag(tag: MetaTag):
    """Create a new tag"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO meta_tags
            (category_id, tag_name, display_name, description, icon, color, is_system_tag, metadata_json)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            tag.category_id, tag.tag_name, tag.display_name, tag.description,
            tag.icon, tag.color, tag.is_system_tag, tag.metadata_json
        ))
        conn.commit()
        return {"tag_id": cursor.lastrowid, "message": "Tag created"}
    except mysql.connector.IntegrityError:
        raise HTTPException(status_code=400, detail="Tag name already exists in category")
    finally:
        cursor.close()
        conn.close()

@router.put("/{tag_id}")
async def update_tag(tag_id: int, tag: MetaTag):
    """Update a tag"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE meta_tags
            SET display_name=%s, description=%s, icon=%s, color=%s, metadata_json=%s
            WHERE tag_id=%s
        """, (tag.display_name, tag.description, tag.icon, tag.color, tag.metadata_json, tag_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Tag not found")
            
        return {"message": "Tag updated"}
    finally:
        cursor.close()
        conn.close()

@router.delete("/{tag_id}")
async def delete_tag(tag_id: int):
    """Delete or deprecate a tag"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Check if tag is assigned to instances
        cursor.execute("SELECT COUNT(*) as count FROM instance_meta_tags WHERE tag_id=%s", (tag_id,))
        result = cursor.fetchone()
        
        if result[0] > 0:
            # Tag is in use - deprecate instead of delete
            cursor.execute("UPDATE meta_tags SET is_deprecated=TRUE WHERE tag_id=%s", (tag_id,))
            conn.commit()
            return {"message": "Tag deprecated (in use by instances)", "deprecated": True}
        else:
            # Safe to delete
            cursor.execute("DELETE FROM meta_tags WHERE tag_id=%s", (tag_id,))
            conn.commit()
            return {"message": "Tag deleted", "deprecated": False}
    finally:
        cursor.close()
        conn.close()

@router.get("/instances/{instance_id}")
async def get_instance_tags(instance_id: str):
    """Get all tags assigned to an instance"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT imt.id, imt.tag_id, t.tag_name, t.display_name, t.icon, t.color,
                   c.category_name, c.display_name as category_display_name,
                   imt.applied_at, imt.applied_by, imt.is_auto_detected, imt.confidence_score
            FROM instance_meta_tags imt
            JOIN meta_tags t ON imt.tag_id = t.tag_id
            JOIN meta_tag_categories c ON t.category_id = c.category_id
            WHERE imt.instance_id = %s
            ORDER BY c.display_order ASC, t.display_name ASC
        """, (instance_id,))
        tags = cursor.fetchall()
        return tags
    finally:
        cursor.close()
        conn.close()

@router.post("/assign")
async def assign_tag_to_instance(assignment: InstanceTagAssignment):
    """Assign a tag to an instance"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO instance_meta_tags 
            (instance_id, tag_id, applied_by, is_auto_detected, confidence_score)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE applied_by=%s, applied_at=NOW()
        """, (
            assignment.instance_id, assignment.tag_id, assignment.applied_by,
            assignment.is_auto_detected, assignment.confidence_score, assignment.applied_by
        ))
        conn.commit()
        
        # Log to history
        cursor.execute("""
            INSERT INTO meta_tag_history (instance_id, tag_id, action, performed_by, reason)
            VALUES (%s, %s, 'added', %s, 'Assigned via web UI')
        """, (assignment.instance_id, assignment.tag_id, assignment.applied_by))
        conn.commit()
        
        return {"message": "Tag assigned to instance"}
    except mysql.connector.IntegrityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cursor.close()
        conn.close()

@router.post("/assign-bulk")
async def assign_tag_bulk(assignment: TagAssignmentBulk):
    """Assign a tag to multiple instances"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        assigned_count = 0
        for instance_id in assignment.instance_ids:
            cursor.execute("""
                INSERT INTO instance_meta_tags (instance_id, tag_id, applied_by)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE applied_by=%s, applied_at=NOW()
            """, (instance_id, assignment.tag_id, assignment.applied_by, assignment.applied_by))
            
            cursor.execute("""
                INSERT INTO meta_tag_history (instance_id, tag_id, action, performed_by, reason)
                VALUES (%s, %s, 'added', %s, 'Bulk assigned via web UI')
            """, (instance_id, assignment.tag_id, assignment.applied_by))
            
            assigned_count += 1
        
        conn.commit()
        return {"message": f"Tag assigned to {assigned_count} instances"}
    finally:
        cursor.close()
        conn.close()

@router.delete("/assign/{instance_id}/{tag_id}")
async def remove_tag_from_instance(instance_id: str, tag_id: int, removed_by: str = "web_ui"):
    """Remove a tag from an instance"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM instance_meta_tags
            WHERE instance_id=%s AND tag_id=%s
        """, (instance_id, tag_id))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Tag assignment not found")
        
        # Log to history
        cursor.execute("""
            INSERT INTO meta_tag_history (instance_id, tag_id, action, performed_by, reason)
            VALUES (%s, %s, 'removed', %s, 'Removed via web UI')
        """, (instance_id, tag_id, removed_by))
        conn.commit()
        
        return {"message": "Tag removed from instance"}
    finally:
        cursor.close()
        conn.close()

@router.get("/dependencies")
async def get_tag_dependencies():
    """Get all tag dependencies"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT td.dependency_id, td.dependent_tag_id, td.required_tag_id,
                   td.dependency_type, td.description,
                   t1.display_name as dependent_tag_name,
                   t2.display_name as required_tag_name
            FROM tag_dependencies td
            JOIN meta_tags t1 ON td.dependent_tag_id = t1.tag_id
            JOIN meta_tags t2 ON td.required_tag_id = t2.tag_id
            ORDER BY t1.display_name ASC
        """)
        deps = cursor.fetchall()
        return deps
    finally:
        cursor.close()
        conn.close()

@router.get("/conflicts")
async def get_tag_conflicts():
    """Get all tag conflicts"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT tc.conflict_id, tc.tag_a_id, tc.tag_b_id,
                   tc.conflict_severity, tc.description,
                   t1.display_name as tag_a_name,
                   t2.display_name as tag_b_name
            FROM tag_conflicts tc
            JOIN meta_tags t1 ON tc.tag_a_id = t1.tag_id
            JOIN meta_tags t2 ON tc.tag_b_id = t2.tag_id
            ORDER BY tc.conflict_severity DESC, t1.display_name ASC
        """)
        conflicts = cursor.fetchall()
        return conflicts
    finally:
        cursor.close()
        conn.close()

@router.get("/usage-stats")
async def get_tag_usage_stats():
    """Get usage statistics for all tags"""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("""
            SELECT t.tag_id, t.display_name, c.category_name,
                   COUNT(imt.instance_id) as usage_count
            FROM meta_tags t
            LEFT JOIN instance_meta_tags imt ON t.tag_id = imt.tag_id
            JOIN meta_tag_categories c ON t.category_id = c.category_id
            WHERE t.is_deprecated = FALSE
            GROUP BY t.tag_id, t.display_name, c.category_name
            ORDER BY usage_count DESC, t.display_name ASC
        """)
        stats = cursor.fetchall()
        return stats
    finally:
        cursor.close()
        conn.close()
