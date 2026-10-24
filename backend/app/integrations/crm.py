"""
CRM Connectors: HubSpot, Salesforce, and Mock CRM
"""

from typing import Any, Dict, List, Optional
import httpx
from datetime import datetime, timezone
import logging

from app.integrations.base import BaseConnector

logger = logging.getLogger(__name__)


class MockCRMConnector(BaseConnector):
    """
    Mock CRM Connector for offline testing, demos, and sandboxing.
    """
    @property
    def provider_name(self) -> str:
        return "mock_crm"

    async def test_connection(self) -> Dict[str, Any]:
        api_key = self.credentials.get("api_key") or self.credentials.get("token")
        if not api_key:
            return {"success": False, "message": "Missing API key or token for Mock CRM"}
        return {
            "success": True,
            "message": "Connected to Mock CRM successfully",
            "account_id": "mock_acc_8849",
            "tier": "enterprise",
            "sync_supported": ["leads", "contacts", "deals"],
        }

    async def sync(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Simulate inbound sync of leads and contacts.
        """
        sample_leads = [
            {
                "external_id": "crm_lead_101",
                "first_name": "Elena",
                "last_name": "Rostova",
                "email": "elena.rostova@enterprisecorp.com",
                "company": "Enterprise Corp",
                "job_title": "VP of Revenue",
                "status": "QUALIFIED",
                "score": 85,
                "notes": "Interested in AI Marketing automation package",
            },
            {
                "external_id": "crm_lead_102",
                "first_name": "Marcus",
                "last_name": "Vance",
                "email": "m.vance@techscale.io",
                "company": "TechScale",
                "job_title": "Head of Demand Gen",
                "status": "CONTACTED",
                "score": 72,
                "notes": "Downloaded Q3 B2B Marketing benchmark report",
            },
        ]
        return {
            "success": True,
            "provider": self.provider_name,
            "records_processed": len(sample_leads),
            "records_failed": 0,
            "leads": sample_leads,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    async def push_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "success": True,
            "external_id": f"mock_lead_{hash(lead_data.get('email', '')) % 10000}",
            "status": "CREATED",
            "lead": lead_data,
        }


class HubSpotConnector(BaseConnector):
    """
    HubSpot CRM Connector using HubSpot REST APIs (Contacts, Deals, Companies).
    Supports token-based or OAuth authentication.
    """
    BASE_URL = "https://api.hubapi.com"

    @property
    def provider_name(self) -> str:
        return "hubspot"

    def _get_headers(self) -> Dict[str, str]:
        token = self.credentials.get("access_token") or self.credentials.get("api_key") or ""
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def test_connection(self) -> Dict[str, Any]:
        token = self.credentials.get("access_token") or self.credentials.get("api_key")
        if not token:
            return {"success": False, "message": "HubSpot access token or API key is required"}
        
        # In test/mock environment or if designated as mock token
        if token.startswith("mock_") or token == "test_token":
            return {
                "success": True,
                "portal_id": 9928120,
                "message": "Connected to HubSpot portal successfully",
                "scopes": ["crm.objects.contacts.read", "crm.objects.contacts.write"],
            }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    f"{self.BASE_URL}/crm/v3/objects/contacts?limit=1",
                    headers=self._get_headers()
                )
                if res.status_code == 200:
                    return {"success": True, "message": "HubSpot connection verified"}
                return {"success": False, "status_code": res.status_code, "message": res.text}
        except Exception as exc:
            return {"success": False, "message": f"HubSpot connection failed: {str(exc)}"}

    async def sync(self, limit: int = 50, **kwargs: Any) -> Dict[str, Any]:
        """
        Pull recent contacts from HubSpot.
        """
        token = self.credentials.get("access_token") or self.credentials.get("api_key") or ""
        if token.startswith("mock_") or token == "test_token":
            # Mocked return for test harnesses
            mock_contacts = [
                {
                    "external_id": "hs_cnt_01",
                    "first_name": "Sarah",
                    "last_name": "Connor",
                    "email": "sconnor@cyberdyne.org",
                    "company": "Cyberdyne Systems",
                    "job_title": "Security Architect",
                    "status": "NEW",
                    "score": 60,
                }
            ]
            return {
                "success": True,
                "provider": self.provider_name,
                "records_processed": len(mock_contacts),
                "records_failed": 0,
                "leads": mock_contacts,
            }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    f"{self.BASE_URL}/crm/v3/objects/contacts?limit={limit}&properties=firstname,lastname,email,company,jobtitle,hs_lead_status",
                    headers=self._get_headers()
                )
                if res.status_code != 200:
                    return {"success": False, "error": res.text, "records_processed": 0, "records_failed": 0}

                data = res.json()
                results = data.get("results", [])
                leads = []
                for item in results:
                    props = item.get("properties", {})
                    leads.append({
                        "external_id": item.get("id"),
                        "first_name": props.get("firstname", ""),
                        "last_name": props.get("lastname", ""),
                        "email": props.get("email", ""),
                        "company": props.get("company", ""),
                        "job_title": props.get("jobtitle", ""),
                        "status": props.get("hs_lead_status", "NEW"),
                    })
                return {
                    "success": True,
                    "provider": self.provider_name,
                    "records_processed": len(leads),
                    "records_failed": 0,
                    "leads": leads,
                }
        except Exception as exc:
            logger.error(f"HubSpot sync error: {exc}")
            return {"success": False, "error": str(exc), "records_processed": 0, "records_failed": 0}

    async def push_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Push contact to HubSpot CRM.
        """
        token = self.credentials.get("access_token") or self.credentials.get("api_key") or ""
        if token.startswith("mock_") or token == "test_token":
            return {"success": True, "external_id": "hs_cnt_created_99", "status": "CREATED"}

        payload = {
            "properties": {
                "firstname": lead_data.get("first_name", ""),
                "lastname": lead_data.get("last_name", ""),
                "email": lead_data.get("email", ""),
                "company": lead_data.get("company", ""),
                "jobtitle": lead_data.get("job_title", ""),
            }
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{self.BASE_URL}/crm/v3/objects/contacts",
                    json=payload,
                    headers=self._get_headers()
                )
                if res.status_code in [200, 201]:
                    data = res.json()
                    return {"success": True, "external_id": data.get("id"), "status": "CREATED"}
                return {"success": False, "error": res.text}
        except Exception as exc:
            return {"success": False, "error": str(exc)}


class SalesforceConnector(BaseConnector):
    """
    Salesforce CRM Connector supporting real Salesforce REST API & OAuth 2.0.
    Supports both Direct Token (OAuth Access Token + Instance URL) and
    Connected App Username-Password flow (Client ID + Client Secret + Username + Password/Security Token).
    """
    API_VERSION = "v58.0"

    @property
    def provider_name(self) -> str:
        return "salesforce"

    async def _resolve_auth(self) -> Dict[str, Any]:
        """
        Resolve or exchange credentials for a live Salesforce instance_url and access_token.
        """
        instance_url = (self.credentials.get("instance_url") or "").rstrip("/")
        access_token = self.credentials.get("access_token") or ""

        # If already provided, return directly
        if instance_url and access_token:
            return {"instance_url": instance_url, "access_token": access_token}

        # Check for Username-Password OAuth Flow
        client_id = self.credentials.get("client_id")
        client_secret = self.credentials.get("client_secret")
        username = self.credentials.get("username")
        password = self.credentials.get("password")
        security_token = self.credentials.get("security_token") or ""
        is_sandbox = self.settings.get("is_sandbox", False)

        if client_id and client_secret and username and password:
            if instance_url:
                token_endpoint = f"{instance_url}/services/oauth2/token"
            elif is_sandbox:
                token_endpoint = "https://test.salesforce.com/services/oauth2/token"
            else:
                token_endpoint = "https://login.salesforce.com/services/oauth2/token"
            full_password = f"{password}{security_token}"
            data = {
                "grant_type": "password",
                "client_id": client_id,
                "client_secret": client_secret,
                "username": username,
                "password": full_password,
            }
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(token_endpoint, data=data)
                    if resp.status_code == 200:
                        payload = resp.json()
                        instance_url = payload.get("instance_url", "").rstrip("/")
                        access_token = payload.get("access_token", "")
                        self.credentials["instance_url"] = instance_url
                        self.credentials["access_token"] = access_token
                        return {"instance_url": instance_url, "access_token": access_token}
                    else:
                        logger.error(f"Salesforce OAuth token failed: {resp.text}")
                        return {"error": f"Salesforce OAuth failed: {resp.text}"}
            except Exception as exc:
                logger.error(f"Salesforce OAuth request exception: {exc}")
                return {"error": str(exc)}

        # Direct SOAP Login Flow (when username & password provided without Connected App client_id/secret)
        if username and password:
            import re
            login_endpoint = (
                "https://test.salesforce.com/services/Soap/u/58.0"
                if is_sandbox
                else "https://login.salesforce.com/services/Soap/u/58.0"
            )
            full_password = f"{password}{security_token}"
            soap_body = f"""<?xml version="1.0" encoding="utf-8" ?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:partner.soap.sforce.com">
  <soapenv:Header/>
  <soapenv:Body>
    <urn:login>
      <urn:username>{username}</urn:username>
      <urn:password>{full_password}</urn:password>
    </urn:login>
  </soapenv:Body>
</soapenv:Envelope>"""
            headers = {
                "Content-Type": "text/xml; charset=UTF-8",
                "SOAPAction": '""',
            }
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(login_endpoint, content=soap_body, headers=headers)
                    if resp.status_code == 200:
                        sid_match = re.search(r"<sessionId>(.*?)</sessionId>", resp.text)
                        url_match = re.search(r"<serverUrl>(.*?)</serverUrl>", resp.text)
                        if sid_match and url_match:
                            access_token = sid_match.group(1)
                            resolved_url = url_match.group(1).split("/services/")[0]
                            instance_url = instance_url or resolved_url
                            self.credentials["instance_url"] = instance_url
                            self.credentials["access_token"] = access_token
                            return {"instance_url": instance_url, "access_token": access_token}
                    else:
                        fault_match = re.search(r"<faultstring>(.*?)</faultstring>", resp.text)
                        err_detail = fault_match.group(1) if fault_match else resp.text
                        logger.error(f"Salesforce SOAP login failed: {err_detail}")
                        return {"error": f"Salesforce login failed: {err_detail}"}
            except Exception as exc:
                logger.error(f"Salesforce SOAP request exception: {exc}")
                return {"error": str(exc)}

        return {"instance_url": instance_url, "access_token": access_token}

    async def test_connection(self) -> Dict[str, Any]:
        auth = await self._resolve_auth()
        if "error" in auth:
            return {"success": False, "message": auth["error"]}

        instance_url = auth.get("instance_url")
        token = auth.get("access_token")

        if token == "test_token" or (token and token.startswith("mock_")):
            return {
                "success": True,
                "message": "Salesforce connection verified (Sandbox / Mock Mode)",
                "instance_url": instance_url or "https://aipnt-demo.my.salesforce.com",
                "api_version": self.API_VERSION,
            }

        if not token or not instance_url:
            return {
                "success": False,
                "message": "Salesforce requires instance_url & access_token, or client_id, client_secret, username, & password.",
            }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.get(
                    f"{instance_url}/services/data/{self.API_VERSION}/limits",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if res.status_code == 200:
                    limits = res.json()
                    daily_api = limits.get("DailyApiRequests", {})
                    return {
                        "success": True,
                        "message": "Connected to live Salesforce CRM successfully",
                        "instance_url": instance_url,
                        "api_version": self.API_VERSION,
                        "api_requests_remaining": daily_api.get("Remaining"),
                        "api_requests_max": daily_api.get("Max"),
                    }
                elif res.status_code == 401:
                    return {"success": False, "status_code": 401, "message": "Salesforce access token expired or invalid"}
                return {"success": False, "status_code": res.status_code, "message": res.text}
        except Exception as exc:
            return {"success": False, "message": f"Salesforce connection error: {str(exc)}"}

    async def sync(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Pull leads from Salesforce via real SOQL query.
        """
        auth = await self._resolve_auth()
        instance_url = auth.get("instance_url")
        token = auth.get("access_token")

        if token == "test_token" or (token and token.startswith("mock_")):
            leads = [
                {
                    "external_id": "sf_lead_001",
                    "first_name": "Devin",
                    "last_name": "Cole",
                    "email": "d.cole@apexglobal.com",
                    "company": "Apex Global",
                    "job_title": "Chief Revenue Officer",
                    "status": "Open - Not Contacted",
                    "score": 92,
                },
                {
                    "external_id": "sf_lead_002",
                    "first_name": "Priya",
                    "last_name": "Sharma",
                    "email": "priya.sharma@medtechsolutions.in",
                    "company": "MedTech Solutions",
                    "job_title": "Director of Growth",
                    "status": "Working - Contacted",
                    "score": 88,
                }
            ]
            return {
                "success": True,
                "provider": self.provider_name,
                "records_processed": len(leads),
                "records_failed": 0,
                "leads": leads,
            }

        if not token or not instance_url:
            return {"success": False, "message": "Missing Salesforce credentials for sync", "records_processed": 0, "records_failed": 0}

        soql = "SELECT Id, FirstName, LastName, Email, Company, Title, Status, LeadSource, CreatedDate FROM Lead WHERE IsConverted = false ORDER BY CreatedDate DESC LIMIT 100"
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                res = await client.get(
                    f"{instance_url}/services/data/{self.API_VERSION}/query",
                    params={"q": soql},
                    headers={"Authorization": f"Bearer {token}"}
                )
                if res.status_code == 200:
                    data = res.json()
                    records = data.get("records", [])
                    leads = []
                    for r in records:
                        leads.append({
                            "external_id": r.get("Id"),
                            "first_name": r.get("FirstName") or "",
                            "last_name": r.get("LastName") or "",
                            "email": r.get("Email") or "",
                            "company": r.get("Company") or "",
                            "job_title": r.get("Title") or "",
                            "status": r.get("Status") or "Open",
                            "score": 75,
                            "lead_source": r.get("LeadSource") or "Salesforce",
                            "created_date": r.get("CreatedDate"),
                        })
                    return {
                        "success": True,
                        "provider": self.provider_name,
                        "records_processed": len(leads),
                        "records_failed": 0,
                        "leads": leads,
                        "total_size": data.get("totalSize", len(leads)),
                    }
                else:
                    logger.error(f"Salesforce query failed: {res.text}")
                    return {"success": False, "error": res.text, "records_processed": 0, "records_failed": 0}
        except Exception as exc:
            logger.error(f"Salesforce sync exception: {exc}")
            return {"success": False, "error": str(exc), "records_processed": 0, "records_failed": 0}

    async def push_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Push new or qualified lead into Salesforce Lead object.
        """
        auth = await self._resolve_auth()
        instance_url = auth.get("instance_url")
        token = auth.get("access_token")

        if token == "test_token" or (token and token.startswith("mock_")):
            return {"success": True, "external_id": "sf_lead_mock_created", "status": "CREATED"}

        if not token or not instance_url:
            return {"success": False, "message": "Missing Salesforce credentials to push lead"}

        payload = {
            "FirstName": lead_data.get("first_name", ""),
            "LastName": lead_data.get("last_name") or "Prospect",
            "Email": lead_data.get("email", ""),
            "Company": lead_data.get("company") or "Independent",
            "Title": lead_data.get("job_title", ""),
            "LeadSource": lead_data.get("source") or lead_data.get("utm_source") or "AIPNT Revenue Platform",
            "Description": lead_data.get("notes") or "Created via AIPNT Agentic Marketing Platform",
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{instance_url}/services/data/{self.API_VERSION}/sobjects/Lead/",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    }
                )
                if res.status_code in [200, 201]:
                    data = res.json()
                    return {
                        "success": True,
                        "external_id": data.get("id"),
                        "status": "CREATED",
                    }
                logger.error(f"Salesforce push lead failed: {res.text}")
                return {"success": False, "error": res.text}
        except Exception as exc:
            logger.error(f"Salesforce push lead exception: {exc}")
            return {"success": False, "error": str(exc)}
