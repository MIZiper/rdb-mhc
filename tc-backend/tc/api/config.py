from fastapi import APIRouter
import os
from tc.auth.keycloak import KC_SERVER_URL, KC_REALM, KC_CLIENT_ID

router = APIRouter(prefix="/config")


@router.get("")
async def get_config():
    return {
        "kc_url": KC_SERVER_URL,
        "kc_realm": KC_REALM,
        "kc_client_id": KC_CLIENT_ID,
        "mh_host": os.getenv("TC_METAHUB", "localhost:8033"),
    }
