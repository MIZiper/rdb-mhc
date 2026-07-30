from fastapi import APIRouter, Depends
import os
from tc.auth.keycloak import KC_SERVER_URL_PUBLIC, KC_REALM, KC_CLIENT_ID, get_optional_user

router = APIRouter(prefix="/config")


@router.get("")
async def get_config(
    user=Depends(get_optional_user),
):
    config = {
        "kc_url": KC_SERVER_URL_PUBLIC,
        "kc_realm": KC_REALM,
        "kc_client_id": KC_CLIENT_ID,
        "mh_host": os.getenv("TC_METAHUB", "localhost:8033"),
    }
    if user is not None:
        config["user_roles"] = list(user.get("roles", []))
        config["user_sub"] = user["sub"]
        config["user_name"] = user["name"]
    return config
