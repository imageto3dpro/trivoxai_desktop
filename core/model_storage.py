"""
Model Storage Manager for Supabase

Stores model file paths/paths (not actual files) in Supabase database.
This is for Supabase Free tier which has limited storage.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List

from core.supabase_client import get_supabase


def save_model_info_to_supabase(
    user_id: str,
    generation_id: str,
    model_files: Dict[str, str],
    input_filename: str,
    processing_method: str = "cloud_api",
) -> Dict[str, Any]:
    """
    Save model file paths/info to Supabase database.

    Note: Actual files stay on user's local machine.
    This just records metadata for admin visibility.

    Args:
        user_id: The user who generated the model
        generation_id: The generation ID from credit_manager
        model_files: Dict with format -> file path (e.g., {"glb": "/path/to/model.glb"})
        input_filename: Original input file name
        processing_method: "local" or "cloud_api"

    Returns:
        Dict with success status and any errors
    """
    sb = get_supabase()
    if not sb:
        return {
            "success": False,
            "error": "Supabase not available",
            "logged": False,
        }

    result = {
        "success": True,
        "logged": True,
        "errors": [],
    }

    try:
        # Build storage info
        storage_files = {}
        total_size = 0

        for format_type, file_path in model_files.items():
            if not file_path or not os.path.exists(file_path):
                result["errors"].append(f"{format_type}: file not found")
                continue

            try:
                file_size = os.path.getsize(file_path)
                total_size += file_size

                storage_files[format_type] = {
                    "path": file_path,
                    "filename": os.path.basename(file_path),
                    "size_bytes": file_size,
                }
            except Exception as e:
                result["errors"].append(f"{format_type}: {str(e)}")

        # Update generation record with storage info
        update_data = {
            "storage_uploaded": True,
            "storage_uploaded_at": datetime.utcnow().isoformat(),
            "storage_files": storage_files,
            "input_filename": input_filename,
            "processing_method": processing_method,
            "total_size_bytes": total_size,
        }

        sb.table("user_generations").update(update_data).eq(
            "id", generation_id
        ).execute()
        print(f"[ModelStorage] Saved model info for generation {generation_id}")

    except Exception as e:
        result["success"] = False
        result["error"] = str(e)
        result["logged"] = False
        print(f"[ModelStorage] Critical error: {e}")

        # Mark as failed in database
        try:
            sb.table("user_generations").update(
                {
                    "storage_uploaded": False,
                    "storage_failed": True,
                    "storage_error": str(e),
                    "storage_attempted_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", generation_id).execute()
        except Exception:
            pass

    return result


def get_user_model_history(user_id: str, limit: int = 50) -> list:
    """
    Get generation history for a specific user.
    """
    sb = get_supabase()
    if not sb:
        return []

    try:
        result = (
            sb.table("user_generations")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"[ModelStorage] Failed to get user history: {e}")
        return []


def get_all_generations_for_admin(
    limit: int = 100,
    offset: int = 0,
) -> list:
    """
    Get all generations for admin review.
    """
    sb = get_supabase()
    if not sb:
        return []

    try:
        result = (
            sb.table("user_generations")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .offset(offset)
            .execute()
        )
        return result.data or []
    except Exception as e:
        print(f"[ModelStorage] Failed to get generations: {e}")
        return []


def get_admin_overview() -> Dict[str, Any]:
    """
    Get admin overview statistics including:
    - Total users
    - Total generations
    - Generations per user
    - Storage usage (file sizes)
    """
    sb = get_supabase()
    if not sb:
        return {
            "total_users": 0,
            "total_generations": 0,
            "generations_per_user": {},
            "storage_usage_mb": 0,
            "by_method": {},
        }

    try:
        # Get all generations
        all_gens = (
            sb.table("user_generations")
            .select("user_id, storage_files, processing_method, created_at")
            .execute()
        ).data or []

        if not all_gens:
            return {
                "total_users": 0,
                "total_generations": 0,
                "generations_per_user": {},
                "storage_usage_mb": 0,
                "by_method": {},
            }

        # Count unique users
        unique_users = set(g["user_id"] for g in all_gens if g.get("user_id"))

        # Count generations per user
        gen_counts = {}
        total_size = 0
        by_method = {}

        for gen in all_gens:
            user_id = gen.get("user_id", "unknown")

            # Count per user
            gen_counts[user_id] = gen_counts.get(user_id, 0) + 1

            # Calculate size
            storage_files = gen.get("storage_files", {})
            if isinstance(storage_files, dict):
                for fmt, info in storage_files.items():
                    if isinstance(info, dict):
                        total_size += info.get("size_bytes", 0)

            # Count by method
            method = gen.get("processing_method", "cloud_api")
            by_method[method] = by_method.get(method, 0) + 1

        # Convert bytes to MB
        storage_mb = total_size / (1024 * 1024)

        return {
            "total_users": len(unique_users),
            "total_generations": len(all_gens),
            "generations_per_user": gen_counts,
            "storage_usage_mb": round(storage_mb, 2),
            "by_method": by_method,
            "recent_generations": all_gens[:10],  # Last 10
        }

    except Exception as e:
        print(f"[ModelStorage] Failed to get admin overview: {e}")
        return {
            "total_users": 0,
            "total_generations": 0,
            "error": str(e),
        }


def get_user_details_for_admin(user_id: str) -> Dict[str, Any]:
    """
    Get detailed info about a specific user including all their generations.
    """
    sb = get_supabase()
    if not sb:
        return {}

    try:
        # Get user info
        user_data = (
            sb.table("web_users")
            .select("id, username, email, created_at, trial_remaining, trial_used")
            .eq("id", user_id)
            .execute()
        ).data

        if not user_data:
            return {"error": "User not found"}

        user = user_data[0]

        # Get all generations for this user
        generations = (
            sb.table("user_generations")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        ).data or []

        # Calculate stats
        total_size = 0
        by_method = {}

        for gen in generations:
            storage_files = gen.get("storage_files", {})
            if isinstance(storage_files, dict):
                for fmt, info in storage_files.items():
                    if isinstance(info, dict):
                        total_size += info.get("size_bytes", 0)

            method = gen.get("processing_method", "cloud_api")
            by_method[method] = by_method.get(method, 0) + 1

        return {
            "user": user,
            "generations": generations,
            "generation_count": len(generations),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_method": by_method,
        }

    except Exception as e:
        print(f"[ModelStorage] Failed to get user details: {e}")
        return {"error": str(e)}


def ensure_storage_columns():
    """
    Print SQL to add required columns (no actual migration needed for metadata only).
    """
    print("[ModelStorage] Required columns for model tracking:")
    print("""
-- Run this in Supabase SQL Editor to enable model tracking:
ALTER TABLE user_generations 
ADD COLUMN IF NOT EXISTS storage_uploaded boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS storage_uploaded_at timestamp with time zone,
ADD COLUMN IF NOT EXISTS storage_files jsonb DEFAULT '{}',
ADD COLUMN IF NOT EXISTS storage_failed boolean DEFAULT false,
ADD COLUMN IF NOT EXISTS storage_error text,
ADD COLUMN IF NOT EXISTS storage_attempted_at timestamp with time zone,
ADD COLUMN IF NOT EXISTS input_filename text,
ADD COLUMN IF NOT EXISTS processing_method text DEFAULT 'cloud_api',
ADD COLUMN IF NOT EXISTS total_size_bytes bigint DEFAULT 0;
    """)
