import datetime
from django.utils import timezone
from ..models import Identity, AccessGrant

def evaluate_access(identity: Identity, resource: str, action: str)->dict:
    """Evaluate access using RBAC+ABAC."""
    now = timezone.now()
    grants = AccessGrant.objects.filter(
        identity=identity,
        is_active=True
    ).select_related("policy")

    context = _build_context(identity)
    
    matched_allow = []
    matched_deny = []
    
    for grant in grants:
        if grant.expires_at and grant.expires_at < now:
            continue
            
        policy = grant.policy
        if not policy.is_active:
            continue
            
        if policy.resource != resource and policy.resource != "*":
            continue
            
        if policy.action != action and policy.action != "admin":
            continue
            
        if policy.conditions and not _match_conditions(policy.conditions, context):
            continue
            
        if policy.effect == "deny":
            matched_deny.append(policy.name)
        else:
            matched_allow.append(policy.name)
            
    if matched_deny:
        return {
            "allowed": False,
            "matched_policies": matched_deny,
            "reason": "Explicit deny"
        }
        
    if matched_allow:
        return {
            "allowed": True,
            "matched_policies": matched_allow,
            "reason": "Explicit allow"
        }
        
    return {
        "allowed": False,
        "matched_policies": [],
        "reason": "Default deny"
    }

def _build_context(identity: Identity, **extra)->dict:
    return {
        "identity_id": str(identity.id),
        "role": identity.role,
        "metadata": identity.metadata,
        "time_hour": timezone.now().hour,
        **extra
    }

def _match_conditions(conditions: dict, context: dict)->bool:
    if "role" in conditions:
        if context.get("role") not in conditions["role"]:
            return False
            
    if "time_start" in conditions and "time_end" in conditions:
        hour = context.get("time_hour", 0)
        if not (conditions["time_start"] <= hour <= conditions["time_end"]):
            return False
            
    if "metadata" in conditions:
        for k, v in conditions["metadata"].items():
            if context.get("metadata", {}).get(k) != v:
                return False
                
    return True
