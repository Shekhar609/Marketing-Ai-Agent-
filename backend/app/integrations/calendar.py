"""
Calendar Connector: Calendly & Google Calendar Real Demo Booking & Meeting Sync
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import httpx
import logging

from app.integrations.base import BaseConnector

logger = logging.getLogger(__name__)


class CalendarConnector(BaseConnector):
    """
    Connects to Calendly or Google Calendar to sync booked demos,
    sales meetings, and prospect consultations for pipeline acceleration.
    Supports real REST APIs for Calendly and Google Calendar.
    """

    @property
    def provider_name(self) -> str:
        return "calendar"

    async def test_connection(self) -> Dict[str, Any]:
        api_key = self.credentials.get("api_key") or self.credentials.get("access_token")
        if not api_key:
            return {"success": False, "message": "Calendar connector requires api_key (Calendly) or access_token (Google Calendar)"}

        provider_type = self.settings.get("type", "calendly").lower()

        if api_key == "test_token" or api_key.startswith("mock_"):
            return {
                "success": True,
                "message": f"Connected to {provider_type.capitalize()} scheduling service (Mock / Sandbox Mode)",
                "provider_type": provider_type,
                "user_email": "sales-team@aipnt.ai",
                "scheduling_url": "https://calendly.com/aipnt-demo",
            }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                if provider_type == "google_calendar" or provider_type == "google":
                    # Google Calendar API Test
                    res = await client.get(
                        "https://www.googleapis.com/calendar/v3/users/me/calendarList",
                        headers={"Authorization": f"Bearer {api_key}"}
                    )
                    if res.status_code == 200:
                        data = res.json()
                        items = data.get("items", [])
                        primary_cal = next((c for c in items if c.get("primary")), items[0] if items else {})
                        return {
                            "success": True,
                            "message": "Connected to Google Calendar successfully",
                            "provider_type": "google_calendar",
                            "calendar_id": primary_cal.get("id"),
                            "summary": primary_cal.get("summary"),
                        }
                    return {"success": False, "status_code": res.status_code, "message": res.text}
                else:
                    # Default Calendly API Test
                    res = await client.get(
                        "https://api.calendly.com/users/me",
                        headers={"Authorization": f"Bearer {api_key}"}
                    )
                    if res.status_code == 200:
                        data = res.json()
                        resource = data.get("resource", {})
                        self.credentials["user_uri"] = resource.get("uri")
                        return {
                            "success": True,
                            "message": "Connected to Calendly successfully",
                            "provider_type": "calendly",
                            "user_name": resource.get("name"),
                            "user_email": resource.get("email"),
                            "scheduling_url": resource.get("scheduling_url"),
                            "organization": resource.get("current_organization"),
                        }
                    return {"success": False, "status_code": res.status_code, "message": res.text}
        except Exception as exc:
            return {"success": False, "message": f"Calendar connection error: {str(exc)}"}

    async def sync(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Pull newly booked sales demos and consultations from Calendly or Google Calendar.
        """
        api_key = self.credentials.get("api_key") or self.credentials.get("access_token")
        provider_type = self.settings.get("type", "calendly").lower()

        if not api_key or api_key == "test_token" or api_key.startswith("mock_"):
            events = [
                {
                    "external_id": "cal_evt_1001",
                    "event_type": "30 Minute AI Growth Platform Demo",
                    "prospect_name": "Elena Rostova",
                    "prospect_email": "elena.rostova@enterprisecorp.com",
                    "scheduled_start": "2026-10-16T15:00:00Z",
                    "status": "CONFIRMED",
                    "utm_source": "linkedin_ad",
                    "utm_campaign": "growth_exec_q3",
                },
                {
                    "external_id": "cal_evt_1002",
                    "event_type": "Executive Revenue Architecture Briefing",
                    "prospect_name": "Devin Cole",
                    "prospect_email": "d.cole@apexglobal.com",
                    "scheduled_start": "2026-10-17T18:00:00Z",
                    "status": "CONFIRMED",
                    "utm_source": "google_search",
                    "utm_campaign": "b2b_intent",
                }
            ]
            return {
                "success": True,
                "provider": self.provider_name,
                "records_processed": len(events),
                "records_failed": 0,
                "events": events,
                "synced_at": datetime.now(timezone.utc).isoformat(),
            }

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                parsed_events: List[Dict[str, Any]] = []

                if provider_type in ["google_calendar", "google"]:
                    # Google Calendar Events
                    now_iso = datetime.now(timezone.utc).isoformat()
                    res = await client.get(
                        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                        params={
                            "singleEvents": "true",
                            "orderBy": "startTime",
                            "timeMin": now_iso,
                            "maxResults": 50,
                        },
                        headers={"Authorization": f"Bearer {api_key}"}
                    )
                    if res.status_code == 200:
                        items = res.json().get("items", [])
                        for item in items:
                            attendees = item.get("attendees", [])
                            prospect_email = attendees[0].get("email", "") if attendees else ""
                            prospect_name = attendees[0].get("displayName", "") if attendees else ""
                            start_time = item.get("start", {}).get("dateTime", item.get("start", {}).get("date", ""))
                            parsed_events.append({
                                "external_id": item.get("id"),
                                "event_type": item.get("summary", "Executive Meeting"),
                                "prospect_name": prospect_name or prospect_email.split("@")[0],
                                "prospect_email": prospect_email,
                                "scheduled_start": start_time,
                                "status": item.get("status", "CONFIRMED").upper(),
                                "utm_source": "calendar_google",
                                "utm_campaign": "direct_booking",
                            })
                    else:
                        logger.error(f"Google Calendar event fetch failed: {res.text}")
                        return {"success": False, "error": res.text, "records_processed": 0, "records_failed": 0}

                else:
                    # Calendly Events
                    user_uri = self.credentials.get("user_uri")
                    if not user_uri:
                        me_res = await client.get(
                            "https://api.calendly.com/users/me",
                            headers={"Authorization": f"Bearer {api_key}"}
                        )
                        if me_res.status_code == 200:
                            user_uri = me_res.json().get("resource", {}).get("uri")
                            self.credentials["user_uri"] = user_uri

                    if user_uri:
                        res = await client.get(
                            "https://api.calendly.com/scheduled_events",
                            params={"user": user_uri, "status": "active", "count": 50},
                            headers={"Authorization": f"Bearer {api_key}"}
                        )
                        if res.status_code == 200:
                            event_items = res.json().get("collection", [])
                            for evt in event_items:
                                evt_uri = evt.get("uri")
                                inv_res = await client.get(
                                    f"{evt_uri}/invitees",
                                    headers={"Authorization": f"Bearer {api_key}"}
                                )
                                prospect_name = "Prospect"
                                prospect_email = ""
                                if inv_res.status_code == 200:
                                    inv_collection = inv_res.json().get("collection", [])
                                    if inv_collection:
                                        prospect_name = inv_collection[0].get("name", "Prospect")
                                        prospect_email = inv_collection[0].get("email", "")

                                parsed_events.append({
                                    "external_id": evt_uri.split("/")[-1] if evt_uri else "cal_evt",
                                    "event_type": evt.get("name", "Demo Booking"),
                                    "prospect_name": prospect_name,
                                    "prospect_email": prospect_email,
                                    "scheduled_start": evt.get("start_time", ""),
                                    "status": evt.get("status", "active").upper(),
                                    "utm_source": "calendly",
                                    "utm_campaign": "inbound_demo",
                                })

                return {
                    "success": True,
                    "provider": self.provider_name,
                    "records_processed": len(parsed_events),
                    "records_failed": 0,
                    "events": parsed_events,
                    "synced_at": datetime.now(timezone.utc).isoformat(),
                }
        except Exception as exc:
            logger.error(f"Calendar sync exception: {exc}")
            return {"success": False, "error": str(exc), "records_processed": 0, "records_failed": 0}

