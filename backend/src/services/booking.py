"""Deterministic business logic for test-drive bookings."""

from __future__ import annotations

import hashlib
import hmac
import csv
import io
import json
import math
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

from src.database import Database


class BookingError(Exception):
    def __init__(self, code: str, message: str, *, retryable: bool = False):
        super().__init__(message); self.code = code; self.retryable = retryable


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


class BookingService:
    def __init__(self, database: Database, *, otp_secret: str = "development-secret", now=utcnow):
        self.db, self.otp_secret, self.now = database, otp_secret.encode(), now

    @staticmethod
    def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row else None

    def _event(self, c, booking_id: str, event: str, actor: str = "system", payload: dict | None = None):
        c.execute("INSERT INTO booking_events VALUES(?,?,?,?,?,?,?)", (_id("evt"), booking_id, event, actor, None, json.dumps(payload or {}), iso(self.now())))

    def resolve_vehicle_model(self, query: str) -> dict:
        with self.db.connect() as c:
            row = c.execute("SELECT * FROM vehicle_models WHERE is_active=1 AND (lower(code)=lower(?) OR lower(name)=lower(?))", (query, query)).fetchone()
            if not row:
                row = c.execute("SELECT * FROM vehicle_models WHERE is_active=1 AND lower(name) LIKE lower(?) ORDER BY name LIMIT 1", (f"%{query}%",)).fetchone()
        if not row: raise BookingError("VEHICLE_NOT_FOUND", "Không tìm thấy mẫu xe.")
        return dict(row)

    def search_options(self, *, vehicle_model: str, vehicle_variant: str | None = None, showroom_id: str | None = None, showroom_query: str | None = None,
                       latitude: float | None = None, longitude: float | None = None, preferred_date: str | None = None, preferred_time: str | None = None, limit: int = 5, **_: Any) -> dict:
        model = self.resolve_vehicle_model(vehicle_model)
        params: list[Any] = [model["id"]]
        variant_sql = ""
        if vehicle_variant:
            variant_sql = " AND (lower(v.code)=lower(?) OR lower(v.name)=lower(?))"; params += [vehicle_variant, vehicle_variant]
        with self.db.connect() as c:
            variants = [dict(r) for r in c.execute("SELECT v.* FROM vehicle_variants v WHERE v.model_id=? AND v.is_active=1" + variant_sql, params)]
            if vehicle_variant and not variants: raise BookingError("VEHICLE_NOT_FOUND", "Không tìm thấy phiên bản xe.")
            variant_ids = [v["id"] for v in variants]
            if not variant_ids: return {"resolved_vehicle": model, "license_requirement": model["required_license_class"], "showrooms": [], "slots": [], "search_stage": "showroom_selection", "missing_fields": []}
            marks = ",".join("?" * len(variant_ids))
            if not showroom_id and showroom_query:
                showroom=c.execute("SELECT id FROM showrooms WHERE is_active=1 AND (lower(code)=lower(?) OR lower(name)=lower(?) OR lower(name) LIKE lower(?) OR lower(address) LIKE lower(?)) ORDER BY CASE WHEN lower(name)=lower(?) THEN 0 ELSE 1 END,name LIMIT 1",(showroom_query,showroom_query,f"%{showroom_query}%",f"%{showroom_query}%",showroom_query)).fetchone()
                if not showroom: raise BookingError("SHOWROOM_NOT_FOUND","Không tìm thấy showroom theo tên hoặc địa chỉ.")
                showroom_id=showroom["id"]
            if not showroom_id:
                rows = c.execute(f"SELECT DISTINCT s.* FROM showrooms s JOIN demo_vehicles d ON d.showroom_id=s.id WHERE s.is_active=1 AND d.is_active=1 AND d.operational_status='available' AND d.variant_id IN ({marks})", variant_ids).fetchall()
                showrooms = [dict(r) for r in rows]
                if latitude is not None and longitude is not None:
                    for s in showrooms: s["distance_km"] = round(self._distance(latitude, longitude, s["latitude"], s["longitude"]), 2)
                    showrooms.sort(key=lambda x: x["distance_km"])
                return {"resolved_vehicle": {**model, "variants": variants}, "license_requirement": model["required_license_class"], "showrooms": showrooms[:limit], "slots": [], "search_stage": "showroom_selection", "missing_fields": []}
            values: list[Any] = [showroom_id, *variant_ids, iso(self.now())]
            date_sql,order_sql = "","s.start_at"
            if preferred_date: date_sql = " AND substr(s.start_at,1,10)=?"; values.append(preferred_date)
            if preferred_time:
                try: hour,minute=(int(x) for x in preferred_time[:5].split(":")); target=hour*60+minute
                except (ValueError,TypeError) as exc: raise BookingError("INVALID_INPUT","Giờ mong muốn phải có định dạng HH:MM.") from exc
                order_sql=f"ABS((CAST(substr(s.start_at,12,2) AS INTEGER)*60 + CAST(substr(s.start_at,15,2) AS INTEGER)) - {target}), s.start_at"
            slots = [dict(r) for r in c.execute(f"SELECT s.*,d.asset_code,v.name variant_name FROM test_drive_slots s JOIN demo_vehicles d ON d.id=s.demo_vehicle_id JOIN vehicle_variants v ON v.id=d.variant_id WHERE s.showroom_id=? AND d.variant_id IN ({marks}) AND s.status='available' AND s.start_at>? {date_sql} ORDER BY {order_sql} LIMIT ?", (*values, min(limit,5)))]
        with self.db.connect() as c:
            selected=self._row(c.execute("SELECT * FROM showrooms WHERE id=?",(showroom_id,)).fetchone())
        return {"resolved_vehicle": {**model, "variants": variants}, "license_requirement": model["required_license_class"], "selected_showroom":selected, "showrooms": [], "slots": slots, "search_stage": "slot_selection", "missing_fields": []}

    @staticmethod
    def _distance(a, b, c, d):
        p1, p2, dl = math.radians(a), math.radians(c), math.radians(d-b)
        x = math.sin((p2-p1)/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
        return 6371 * 2 * math.atan2(math.sqrt(x), math.sqrt(1-x))

    def hold_slot(self, slot_id: str, ui_action_id: str, *, ttl_seconds: int = 900, source_channel: str = "web") -> dict:
        with self.db.transaction(immediate=True) as c:
            cached = c.execute("SELECT response_json FROM idempotency_records WHERE action_id=?", (ui_action_id,)).fetchone()
            if cached: return json.loads(cached[0])
            slot = c.execute("SELECT s.*,v.required_license_class FROM test_drive_slots s JOIN demo_vehicles d ON d.id=s.demo_vehicle_id JOIN vehicle_variants x ON x.id=d.variant_id JOIN vehicle_models v ON v.id=x.model_id WHERE s.id=?", (slot_id,)).fetchone()
            if not slot or slot["status"] != "available": raise BookingError("SLOT_NO_LONGER_AVAILABLE", "Slot không còn khả dụng.", retryable=True)
            overlap = c.execute("SELECT 1 FROM test_drive_slots WHERE demo_vehicle_id=? AND id<>? AND start_at<? AND end_at>? AND status IN ('held','booked','blocked') LIMIT 1", (slot["demo_vehicle_id"], slot_id, slot["end_at"], slot["start_at"])).fetchone()
            if overlap: raise BookingError("SLOT_NO_LONGER_AVAILABLE", "Xe demo đã có lịch trùng.", retryable=True)
            now, expires, booking_id = self.now(), self.now()+timedelta(seconds=ttl_seconds), _id("bkg")
            c.execute("INSERT INTO bookings(id,slot_id,status,held_at,hold_expires_at,source_channel,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)", (booking_id,slot_id,"held",iso(now),iso(expires),source_channel,iso(now),iso(now)))
            c.execute("UPDATE test_drive_slots SET status='held',held_until=?,current_booking_id=?,updated_at=? WHERE id=?", (iso(expires),booking_id,iso(now),slot_id))
            c.execute("INSERT INTO booking_driver_details(booking_id,required_license_class,created_at,updated_at) VALUES(?,?,?,?)", (booking_id,slot["required_license_class"],iso(now),iso(now)))
            c.execute("INSERT INTO notification_plans(booking_id,created_at,updated_at) VALUES(?,?,?)", (booking_id,iso(now),iso(now)))
            self._event(c, booking_id, "slot_held", "user", {"slot_id": slot_id})
            result = {"booking_id": booking_id, "status": "held", "hold_expires_at": iso(expires), "remaining_seconds": ttl_seconds}
            c.execute("INSERT INTO idempotency_records VALUES(?,?,?,?)", (ui_action_id,"hold_slot",json.dumps(result),iso(now)))
            return result

    def _draft(self, c, booking_id: str) -> dict:
        booking = self._row(c.execute("SELECT * FROM bookings WHERE id=?",(booking_id,)).fetchone())
        if not booking: raise BookingError("BOOKING_NOT_FOUND", "Không tìm thấy booking.")
        booking["booker"] = self._row(c.execute("SELECT * FROM people WHERE id=?",(booking["booker_person_id"],)).fetchone()) if booking["booker_person_id"] else None
        booking["driver"] = self._row(c.execute("SELECT * FROM people WHERE id=?",(booking["driver_person_id"],)).fetchone()) if booking["driver_person_id"] else None
        booking["license_declaration"] = self._row(c.execute("SELECT * FROM booking_driver_details WHERE booking_id=?",(booking_id,)).fetchone())
        booking["notification_plan"] = self._row(c.execute("SELECT * FROM notification_plans WHERE booking_id=?",(booking_id,)).fetchone())
        missing = []
        for role in ("booker","driver"):
            if not booking[role]: missing.append(role)
            elif not booking[role]["phone"] and not booking[role]["email"]: missing.append(f"{role}.contact")
        lic=booking["license_declaration"]
        for field in ("license_number","declared_license_class"):
            if not lic.get(field): missing.append(f"license.{field}")
        if not lic["validity_acknowledged"]: missing.append("license.validity_acknowledged")
        remaining=max(0,int((datetime.fromisoformat(booking["hold_expires_at"])-self.now()).total_seconds()))
        booking.update(missing_required_fields=missing,validation_warnings=[],remaining_seconds=remaining,is_ready_to_confirm=not missing and remaining>0)
        return booking

    def get_booking_draft(self, booking_id: str) -> dict:
        with self.db.connect() as c: return self._draft(c,booking_id)

    def update_booking_draft(self, booking_id: str, *, booker_patch=None, driver_patch=None, driver_same_as_booker: bool = False, license_patch=None, notification_plan_patch=None, expected_version=None) -> dict:
        with self.db.transaction(immediate=True) as c:
            b=c.execute("SELECT * FROM bookings WHERE id=?",(booking_id,)).fetchone()
            if not b: raise BookingError("BOOKING_NOT_FOUND","Không tìm thấy booking.")
            if b["status"]!="held" or datetime.fromisoformat(b["hold_expires_at"])<=self.now(): raise BookingError("HOLD_EXPIRED","Hold đã hết hạn.")
            if expected_version is not None and b["version"]!=expected_version: raise BookingError("VERSION_CONFLICT","Draft đã được cập nhật ở nơi khác.",retryable=True)
            for role, patch in (("booker",booker_patch),("driver",None if driver_same_as_booker else driver_patch)):
                if patch:
                    allowed={k:patch.get(k) for k in ("full_name","phone","email","preferred_channel") if k in patch}
                    if not allowed.get("full_name"): raise BookingError("INVALID_INPUT",f"{role}.full_name là bắt buộc.")
                    pid=b[f"{role}_person_id"] or _id("person"); now=iso(self.now())
                    if b[f"{role}_person_id"]:
                        sets=",".join(f"{k}=?" for k in allowed); c.execute(f"UPDATE people SET {sets},updated_at=? WHERE id=?",(*allowed.values(),now,pid))
                    else:
                        c.execute("INSERT INTO people(id,full_name,phone,email,preferred_channel,normalized_phone,normalized_email,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",(pid,allowed["full_name"],allowed.get("phone"),allowed.get("email"),allowed.get("preferred_channel","sms"),allowed.get("phone"),allowed.get("email","").lower() or None,now,now)); c.execute(f"UPDATE bookings SET {role}_person_id=? WHERE id=?",(pid,booking_id))
            if driver_same_as_booker:
                booker_id=c.execute("SELECT booker_person_id FROM bookings WHERE id=?",(booking_id,)).fetchone()[0]
                if not booker_id: raise BookingError("INVALID_INPUT","Cần nhập thông tin Booker trước.")
                c.execute("UPDATE bookings SET driver_person_id=? WHERE id=?",(booker_id,booking_id))
            if license_patch:
                allowed={k:v for k,v in license_patch.items() if k in ("license_number","declared_license_class","validity_acknowledged")}
                if allowed: c.execute("UPDATE booking_driver_details SET "+",".join(f"{k}=?" for k in allowed)+",updated_at=? WHERE booking_id=?",(*allowed.values(),iso(self.now()),booking_id))
            if notification_plan_patch:
                allowed={k:v for k,v in notification_plan_patch.items() if k in ("copy_booker","sms_enabled","email_enabled","reminder_24h_enabled","reminder_2h_enabled")}
                if allowed: c.execute("UPDATE notification_plans SET "+",".join(f"{k}=?" for k in allowed)+",updated_at=? WHERE booking_id=?",(*allowed.values(),iso(self.now()),booking_id))
            c.execute("UPDATE bookings SET version=version+1,updated_at=? WHERE id=?",(iso(self.now()),booking_id)); self._event(c,booking_id,"booking_draft_updated","agent")
            return self._draft(c,booking_id)

    def confirm_booking(self, booking_id: str, ui_action_id: str, expected_version: int) -> dict:
        with self.db.transaction(immediate=True) as c:
            cached=c.execute("SELECT response_json FROM idempotency_records WHERE action_id=?",(ui_action_id,)).fetchone()
            if cached:return json.loads(cached[0])
            draft=self._draft(c,booking_id)
            if draft["status"]!="held" or draft["remaining_seconds"]<=0: raise BookingError("HOLD_EXPIRED","Hold đã hết hạn.")
            if draft["version"]!=expected_version: raise BookingError("VERSION_CONFLICT","Draft đã thay đổi.",retryable=True)
            if not draft["is_ready_to_confirm"]: raise BookingError("INVALID_INPUT","Draft chưa đủ thông tin.")
            slot=c.execute("SELECT * FROM test_drive_slots WHERE id=?",(draft["slot_id"],)).fetchone()
            if slot["status"]!="held" or slot["current_booking_id"]!=booking_id: raise BookingError("SLOT_NO_LONGER_AVAILABLE","Slot không thuộc booking.")
            code="VF"+self.now().strftime("%y%m%d")+secrets.token_hex(3).upper(); now=iso(self.now())
            c.execute("UPDATE bookings SET status='confirmed',booking_code=?,confirmed_at=?,version=version+1,updated_at=? WHERE id=?",(code,now,now,booking_id)); c.execute("UPDATE test_drive_slots SET status='booked',held_until=NULL,updated_at=? WHERE id=?",(now,draft["slot_id"])); c.execute("UPDATE booking_driver_details SET license_check_status='pending_in_person',updated_at=? WHERE booking_id=?",(now,booking_id))
            self._create_jobs(c,booking_id,draft["driver_person_id"],slot["start_at"]); self._event(c,booking_id,"booking_confirmed","user")
            result={"booking_id":booking_id,"booking_code":code,"status":"confirmed","confirmed_at":now}; c.execute("INSERT INTO idempotency_records VALUES(?,?,?,?)",(ui_action_id,"confirm_booking",json.dumps(result),now)); return result

    def _create_jobs(self,c,bid,recipient,start):
        start_dt=datetime.fromisoformat(start); now=iso(self.now())
        for typ,when in (("booking_confirmation",self.now()),("reminder_24h",start_dt-timedelta(hours=24)),("reminder_2h",start_dt-timedelta(hours=2))):
            c.execute("INSERT INTO notification_jobs(id,booking_id,recipient_person_id,notification_type,channel,scheduled_at,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",(_id("job"),bid,recipient,typ,"sms",iso(when),now,now))

    def request_access(self, booking_code: str, contact_value: str, purpose: str, preferred_channel: str = "sms", *, expose_otp: bool = False) -> dict:
        permissions={"lookup":["read_booking"],"reschedule":["read_booking","reschedule_booking"],"cancel":["read_booking","cancel_booking"],"update_details":["read_booking","update_details"],"update_notifications":["read_booking","update_notifications"]}
        if purpose not in permissions: raise BookingError("INVALID_INPUT","Purpose không hợp lệ.")
        normalized=contact_value.strip().lower()
        with self.db.transaction(immediate=True) as c:
            b=c.execute("SELECT DISTINCT b.* FROM bookings b JOIN people p ON p.id IN (b.booker_person_id,b.driver_person_id) WHERE b.booking_code=? AND (lower(p.email)=? OR p.phone=?)",(booking_code,normalized,contact_value.strip())).fetchone()
            if not b: raise BookingError("BOOKING_NOT_FOUND","Không tìm thấy booking phù hợp.")
            code=f"{secrets.randbelow(1000000):06d}"; salt=secrets.token_hex(8); digest=self._hash(code,salt); challenge=_id("otp"); expires=self.now()+timedelta(minutes=5); masked=self._mask(contact_value)
            c.execute("INSERT INTO otp_challenges(id,booking_id,purpose,channel,destination_masked,destination_hash,code_hash,expires_at,created_at) VALUES(?,?,?,?,?,?,?,?,?)",(challenge,b["id"],purpose,preferred_channel,masked,self._hash(normalized,"destination"),salt+":"+digest,iso(expires),iso(self.now()))); self._event(c,b["id"],"otp_requested","user",{"purpose":purpose})
        result={"challenge_id":challenge,"destination_masked":masked,"expires_at":iso(expires),"retry_after_seconds":60};
        if expose_otp: result["otp_code"]=code
        return result

    def _hash(self,value,salt): return hmac.new(self.otp_secret,(salt+value).encode(),hashlib.sha256).hexdigest()
    @staticmethod
    def _mask(v):
        if "@" in v: a,b=v.split("@",1); return a[:1]+"***@"+b
        return "*"*max(0,len(v)-3)+v[-3:]

    def verify_access(self, challenge_id: str, otp_code: str) -> dict:
        with self.db.transaction(immediate=True) as c:
            ch=c.execute("SELECT * FROM otp_challenges WHERE id=?",(challenge_id,)).fetchone()
            if not ch: raise BookingError("OTP_INVALID","OTP không hợp lệ.")
            if ch["status"]!="pending": raise BookingError("OTP_LOCKED" if ch["status"]=="locked" else "OTP_INVALID","OTP không còn dùng được.")
            if datetime.fromisoformat(ch["expires_at"])<=self.now(): c.execute("UPDATE otp_challenges SET status='expired' WHERE id=?",(challenge_id,)); raise BookingError("OTP_EXPIRED","OTP đã hết hạn.")
            salt,digest=ch["code_hash"].split(":",1)
            if not hmac.compare_digest(self._hash(otp_code,salt),digest):
                attempts=ch["attempt_count"]+1; status="locked" if attempts>=ch["max_attempts"] else "pending"; c.execute("UPDATE otp_challenges SET attempt_count=?,status=? WHERE id=?",(attempts,status,challenge_id)); raise BookingError("OTP_LOCKED" if status=="locked" else "OTP_INVALID","OTP không đúng.")
            now=iso(self.now()); c.execute("UPDATE otp_challenges SET status='verified',verified_at=? WHERE id=?",(now,challenge_id)); raw=secrets.token_urlsafe(32); token_hash=self._hash(raw,"session"); perms={"lookup":["read_booking"],"reschedule":["read_booking","reschedule_booking"],"cancel":["read_booking","cancel_booking"],"update_details":["read_booking","update_details"],"update_notifications":["read_booking","update_notifications"]}[ch["purpose"]]; expiry=self.now()+timedelta(minutes=30)
            c.execute("INSERT INTO booking_access_sessions VALUES(?,?,?,?,?,?,?,?)",(_id("session"),token_hash,ch["booking_id"],challenge_id,json.dumps(perms),iso(expiry),None,now)); self._event(c,ch["booking_id"],"otp_verified","user")
            return {"access_session_token":raw,"booking_id":ch["booking_id"],"permissions":perms,"session_expires_at":iso(expiry)}

    def get_booking_details(self, access_session_token: str, *, booking_id: str | None = None, booking_code: str | None = None) -> dict:
        with self.db.connect() as c:
            session=c.execute("SELECT * FROM booking_access_sessions WHERE token_hash=?",(self._hash(access_session_token,"session"),)).fetchone()
            if not session or session["revoked_at"] or datetime.fromisoformat(session["expires_at"])<=self.now(): raise BookingError("ACCESS_SESSION_EXPIRED","Phiên truy cập đã hết hạn.")
            if "read_booking" not in json.loads(session["permissions_json"]): raise BookingError("ACCESS_DENIED","Không có quyền đọc booking.")
            b=c.execute("SELECT * FROM bookings WHERE id=?",(session["booking_id"],)).fetchone()
            if (booking_id and booking_id!=b["id"]) or (booking_code and booking_code!=b["booking_code"]): raise BookingError("ACCESS_DENIED","Phiên không thuộc booking này.")
            result=self._draft(c,b["id"]); result["slot"]=self._row(c.execute("SELECT * FROM test_drive_slots WHERE id=?",(b["slot_id"],)).fetchone())
            catalog=c.execute("SELECT m.*,v.id variant_id,v.name variant_name,s.name showroom_name FROM test_drive_slots t JOIN demo_vehicles d ON d.id=t.demo_vehicle_id JOIN vehicle_variants v ON v.id=d.variant_id JOIN vehicle_models m ON m.id=v.model_id JOIN showrooms s ON s.id=t.showroom_id WHERE t.id=?",(b["slot_id"],)).fetchone()
            result["vehicle"]=self._row(catalog); result["showroom"]={"id":result["slot"]["showroom_id"],"name":catalog["showroom_name"]}; result["allowed_actions"]=json.loads(session["permissions_json"]); return result

    def _require_access(self, c, token: str, booking_id: str, permission: str) -> sqlite3.Row:
        session=c.execute("SELECT * FROM booking_access_sessions WHERE token_hash=?",(self._hash(token,"session"),)).fetchone()
        if not session or session["revoked_at"] or datetime.fromisoformat(session["expires_at"])<=self.now():
            raise BookingError("ACCESS_SESSION_EXPIRED","Phiên truy cập đã hết hạn.")
        if session["booking_id"] != booking_id or permission not in json.loads(session["permissions_json"]):
            raise BookingError("ACCESS_DENIED","Phiên không có quyền thực hiện thao tác này.")
        return session

    def update_booking_details(self, booking_id: str, access_session_token: str, *, booker_patch=None, driver_patch=None) -> dict:
        """Edit people data of an existing booking after OTP verification."""
        with self.db.transaction(immediate=True) as c:
            self._require_access(c,access_session_token,booking_id,"update_details")
            booking=c.execute("SELECT * FROM bookings WHERE id=?",(booking_id,)).fetchone()
            if not booking or booking["status"] not in ("confirmed","checked_in"):
                raise BookingError("BOOKING_NOT_EDITABLE","Booking không thể chỉnh sửa.")
            for role,patch in (("booker",booker_patch),("driver",driver_patch)):
                if not patch: continue
                pid=booking[f"{role}_person_id"]
                allowed={k:v for k,v in patch.items() if k in ("full_name","phone","email","preferred_channel")}
                if allowed:
                    c.execute("UPDATE people SET "+",".join(f"{k}=?" for k in allowed)+",updated_at=? WHERE id=?",(*allowed.values(),iso(self.now()),pid))
            c.execute("UPDATE bookings SET version=version+1,updated_at=? WHERE id=?",(iso(self.now()),booking_id))
            self._event(c,booking_id,"booking_details_updated","user")
            return self._draft(c,booking_id)

    def hold_reschedule_slot(self, current_booking_id: str, new_slot_id: str, access_session_token: str, ui_action_id: str) -> dict:
        with self.db.connect() as c:
            self._require_access(c,access_session_token,current_booking_id,"reschedule_booking")
            current=c.execute("SELECT status FROM bookings WHERE id=?",(current_booking_id,)).fetchone()
            if not current or current["status"]!="confirmed": raise BookingError("BOOKING_NOT_EDITABLE","Booking không thể dời lịch.")
        held=self.hold_slot(new_slot_id,ui_action_id,source_channel="reschedule")
        with self.db.transaction(immediate=True) as c:
            current=c.execute("SELECT * FROM bookings WHERE id=?",(current_booking_id,)).fetchone()
            c.execute("UPDATE bookings SET rescheduled_from_booking_id=?,booker_person_id=?,driver_person_id=?,updated_at=? WHERE id=?",(current_booking_id,current["booker_person_id"],current["driver_person_id"],iso(self.now()),held["booking_id"]))
            old_detail=c.execute("SELECT * FROM booking_driver_details WHERE booking_id=?",(current_booking_id,)).fetchone()
            if old_detail:
                c.execute("UPDATE booking_driver_details SET license_number=?,declared_license_class=?,validity_acknowledged=?,license_check_status='pending_in_person',updated_at=? WHERE booking_id=?",(old_detail["license_number"],old_detail["declared_license_class"],old_detail["validity_acknowledged"],iso(self.now()),held["booking_id"]))
            old_plan=c.execute("SELECT * FROM notification_plans WHERE booking_id=?",(current_booking_id,)).fetchone()
            if old_plan:
                c.execute("UPDATE notification_plans SET primary_recipient_role=?,copy_booker=?,sms_enabled=?,email_enabled=?,reminder_24h_enabled=?,reminder_2h_enabled=?,custom_plan_json=?,updated_at=? WHERE booking_id=?",(old_plan["primary_recipient_role"],old_plan["copy_booker"],old_plan["sms_enabled"],old_plan["email_enabled"],old_plan["reminder_24h_enabled"],old_plan["reminder_2h_enabled"],old_plan["custom_plan_json"],iso(self.now()),held["booking_id"]))
            self._event(c,held["booking_id"],"reschedule_slot_held","user",{"current_booking_id":current_booking_id})
        return {**held,"current_booking_id":current_booking_id}

    def confirm_reschedule(self, current_booking_id: str, new_booking_id: str, access_session_token: str, ui_action_id: str) -> dict:
        with self.db.transaction(immediate=True) as c:
            cached=c.execute("SELECT response_json FROM idempotency_records WHERE action_id=?",(ui_action_id,)).fetchone()
            if cached:return json.loads(cached[0])
            self._require_access(c,access_session_token,current_booking_id,"reschedule_booking")
            old=c.execute("SELECT * FROM bookings WHERE id=?",(current_booking_id,)).fetchone(); new=c.execute("SELECT * FROM bookings WHERE id=?",(new_booking_id,)).fetchone()
            if not old or old["status"]!="confirmed" or not new or new["status"]!="held" or new["rescheduled_from_booking_id"]!=current_booking_id:
                raise BookingError("BOOKING_NOT_EDITABLE","Cặp booking dời lịch không hợp lệ.")
            if datetime.fromisoformat(new["hold_expires_at"])<=self.now(): raise BookingError("HOLD_EXPIRED","Hold lịch mới đã hết hạn.")
            new_slot=c.execute("SELECT * FROM test_drive_slots WHERE id=?",(new["slot_id"],)).fetchone()
            if new_slot["current_booking_id"]!=new_booking_id: raise BookingError("SLOT_NO_LONGER_AVAILABLE","Slot mới không còn thuộc booking.")
            now=iso(self.now()); code="VF"+self.now().strftime("%y%m%d")+secrets.token_hex(3).upper()
            c.execute("UPDATE bookings SET status='confirmed',booking_code=?,confirmed_at=?,version=version+1,updated_at=? WHERE id=?",(code,now,now,new_booking_id))
            c.execute("UPDATE test_drive_slots SET status='booked',held_until=NULL,updated_at=? WHERE id=?",(now,new["slot_id"]))
            c.execute("UPDATE bookings SET status='rescheduled',replaced_by_booking_id=?,version=version+1,updated_at=? WHERE id=?",(new_booking_id,now,current_booking_id))
            c.execute("UPDATE test_drive_slots SET status='available',current_booking_id=NULL,held_until=NULL,updated_at=? WHERE id=? AND current_booking_id=?",(now,old["slot_id"],current_booking_id))
            c.execute("UPDATE notification_jobs SET status='cancelled',updated_at=? WHERE booking_id=? AND status='pending'",(now,current_booking_id))
            self._create_jobs(c,new_booking_id,new["driver_person_id"],new_slot["start_at"])
            self._event(c,current_booking_id,"booking_rescheduled","user",{"new_booking_id":new_booking_id}); self._event(c,new_booking_id,"booking_confirmed","user",{"old_booking_id":current_booking_id})
            result={"old_booking_status":"rescheduled","new_booking_status":"confirmed","new_booking_id":new_booking_id,"new_booking_code":code,"released_old_slot_id":old["slot_id"]}
            c.execute("INSERT INTO idempotency_records VALUES(?,?,?,?)",(ui_action_id,"confirm_reschedule",json.dumps(result),now)); return result

    def cancel_booking(self, booking_id: str, access_session_token: str, ui_action_id: str, reason: str | None = None) -> dict:
        with self.db.transaction(immediate=True) as c:
            cached=c.execute("SELECT response_json FROM idempotency_records WHERE action_id=?",(ui_action_id,)).fetchone()
            if cached:return json.loads(cached[0])
            self._require_access(c,access_session_token,booking_id,"cancel_booking")
            b=c.execute("SELECT * FROM bookings WHERE id=?",(booking_id,)).fetchone()
            if not b or b["status"]!="confirmed": raise BookingError("BOOKING_NOT_CANCELLABLE","Booking không thể hủy.")
            now=iso(self.now()); c.execute("UPDATE bookings SET status='cancelled',cancelled_at=?,cancellation_reason=?,version=version+1,updated_at=? WHERE id=?",(now,reason,now,booking_id)); c.execute("UPDATE test_drive_slots SET status='available',current_booking_id=NULL,held_until=NULL,updated_at=? WHERE id=? AND current_booking_id=?",(now,b["slot_id"],booking_id)); jobs=c.execute("UPDATE notification_jobs SET status='cancelled',updated_at=? WHERE booking_id=? AND status='pending'",(now,booking_id)).rowcount; self._event(c,booking_id,"booking_cancelled","user",{"reason":reason})
            result={"booking_status":"cancelled","released_slot_id":b["slot_id"],"cancelled_notification_jobs_count":jobs}; c.execute("INSERT INTO idempotency_records VALUES(?,?,?,?)",(ui_action_id,"cancel_booking",json.dumps(result),now)); return result

    def import_showrooms_csv(self, csv_text: str) -> dict:
        """Upsert showroom rows from a UTF-8 CSV document."""
        required={"code","name","address","latitude","longitude"}; reader=csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")))
        if not reader.fieldnames or not required.issubset(reader.fieldnames): raise BookingError("INVALID_INPUT","CSV thiếu cột bắt buộc: code,name,address,latitude,longitude.")
        imported=0
        with self.db.transaction(immediate=True) as c:
            for line,row in enumerate(reader,start=2):
                try: lat,lon=float(row["latitude"]),float(row["longitude"])
                except ValueError as exc: raise BookingError("INVALID_INPUT",f"Tọa độ không hợp lệ tại dòng {line}.") from exc
                now=iso(self.now()); existing=c.execute("SELECT id FROM showrooms WHERE code=?",(row["code"].strip(),)).fetchone(); sid=existing["id"] if existing else _id("showroom")
                c.execute("INSERT INTO showrooms(id,code,name,address,latitude,longitude,phone,email,timezone,is_active,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(code) DO UPDATE SET name=excluded.name,address=excluded.address,latitude=excluded.latitude,longitude=excluded.longitude,phone=excluded.phone,email=excluded.email,timezone=excluded.timezone,is_active=excluded.is_active,updated_at=excluded.updated_at",(sid,row["code"].strip(),row["name"].strip(),row["address"].strip(),lat,lon,row.get("phone") or None,row.get("email") or None,row.get("timezone") or "Asia/Ho_Chi_Minh",0 if str(row.get("is_active","1")).lower() in ("0","false","no") else 1,now,now)); imported+=1
        return {"imported":imported}

    DATASET_FILES = {
        "01_vehicle_models.csv": ("vehicle_models", ["id","code","name","vehicle_type","required_license_class","license_requirement_note","is_active","created_at","updated_at"]),
        "02_vehicle_variants.csv": ("vehicle_variants", ["id","model_id","code","name","battery_capacity_kwh","estimated_range_km","motor_power_kw","is_active","created_at","updated_at"]),
        "03_showrooms.csv": ("showrooms", ["id","code","name","address","latitude","longitude","phone","email","timezone","is_active","created_at","updated_at"]),
        "04_sales_staff.csv": ("sales_staff", ["id","showroom_id","employee_code","full_name","phone","email","status","created_at","updated_at"]),
        "05_demo_vehicles.csv": ("demo_vehicles", ["id","showroom_id","variant_id","asset_code","vin","plate_number","operational_status","battery_soc","minimum_booking_soc","charging_status","is_active","created_at","updated_at"]),
        # normalized_phone/email are database-only nullable derivatives, not mock CSV fields.
        "08_people.csv": ("people", ["id","full_name","phone","email","preferred_channel","created_at","updated_at"]),
        "06_test_drive_slots.csv": ("test_drive_slots", ["id","showroom_id","demo_vehicle_id","start_at","end_at","status","held_until","current_booking_id","block_reason","created_at","updated_at"]),
        "09_bookings.csv": ("bookings", ["id","booking_code","slot_id","booker_person_id","driver_person_id","status","held_at","hold_expires_at","confirmed_at","checked_in_at","completed_at","cancelled_at","cancellation_reason","rescheduled_from_booking_id","replaced_by_booking_id","source_channel","version","created_at","updated_at"]),
        "07_slot_sales_assignments.csv": ("slot_sales_assignments", ["id","slot_id","sales_staff_id","assignment_role","status","created_at","updated_at"]),
        "10_booking_driver_details.csv": ("booking_driver_details", ["booking_id","license_number","declared_license_class","required_license_class","validity_acknowledged","license_check_status","checked_at","checked_by","rejection_reason","created_at","updated_at"]),
        "11_notification_plans.csv": ("notification_plans", ["booking_id","primary_recipient_role","copy_booker","sms_enabled","email_enabled","reminder_24h_enabled","reminder_2h_enabled","custom_plan_json","created_at","updated_at"]),
        "12_notification_jobs.csv": ("notification_jobs", ["id","booking_id","recipient_person_id","notification_type","channel","scheduled_at","status","sent_at","provider_message_id","attempt_count","error_message","created_at","updated_at"]),
        "13_otp_challenges.csv": ("otp_challenges", ["id","booking_id","purpose","channel","destination_masked","destination_hash","code_hash","expires_at","attempt_count","max_attempts","resend_count","status","verified_at","created_at"]),
        # token_hash is generated during import because mock sessions contain no usable raw token.
        "14_booking_access_sessions.csv": ("booking_access_sessions", ["id","booking_id","otp_challenge_id","permissions_json","expires_at","revoked_at","created_at"]),
        "15_booking_events.csv": ("booking_events", ["id","booking_id","event_type","actor_type","actor_id","payload_json","created_at"]),
    }

    DATASET_REFERENCES = {
        "02_vehicle_variants.csv": (("model_id","vehicle_models","id","01_vehicle_models.csv"),),
        "04_sales_staff.csv": (("showroom_id","showrooms","id","03_showrooms.csv"),),
        "05_demo_vehicles.csv": (("showroom_id","showrooms","id","03_showrooms.csv"),("variant_id","vehicle_variants","id","02_vehicle_variants.csv")),
        "06_test_drive_slots.csv": (("showroom_id","showrooms","id","03_showrooms.csv"),("demo_vehicle_id","demo_vehicles","id","05_demo_vehicles.csv")),
        "09_bookings.csv": (("slot_id","test_drive_slots","id","06_test_drive_slots.csv"),("booker_person_id","people","id","08_people.csv"),("driver_person_id","people","id","08_people.csv")),
        "07_slot_sales_assignments.csv": (("slot_id","test_drive_slots","id","06_test_drive_slots.csv"),("sales_staff_id","sales_staff","id","04_sales_staff.csv")),
        "10_booking_driver_details.csv": (("booking_id","bookings","id","09_bookings.csv"),),
        "11_notification_plans.csv": (("booking_id","bookings","id","09_bookings.csv"),),
        "12_notification_jobs.csv": (("booking_id","bookings","id","09_bookings.csv"),("recipient_person_id","people","id","08_people.csv")),
        "13_otp_challenges.csv": (("booking_id","bookings","id","09_bookings.csv"),),
        "14_booking_access_sessions.csv": (("booking_id","bookings","id","09_bookings.csv"),("otp_challenge_id","otp_challenges","id","13_otp_challenges.csv")),
        "15_booking_events.csv": (("booking_id","bookings","id","09_bookings.csv"),),
    }

    @staticmethod
    def _assert_dataset_references(c,filename,rows,references):
        problems=[]
        for column,parent_table,parent_column,parent_file in references:
            values={row[column] for row in rows if row[column]}
            if not values: continue
            marks=",".join("?"*len(values)); found={r[0] for r in c.execute(f"SELECT {parent_column} FROM {parent_table} WHERE {parent_column} IN ({marks})",tuple(values))}
            missing=sorted(values-found)
            if missing:
                preview=", ".join(missing[:5])+(f" (+{len(missing)-5} ID khác)" if len(missing)>5 else "")
                problems.append(f"{column} thiếu trong {parent_table}: {preview}; hãy import {parent_file} trước/cùng lúc")
        if problems: raise BookingError("MISSING_DEPENDENCY",f"Không thể import {filename}: "+" | ".join(problems))

    def import_eval_dataset(self, files: dict[str, str]) -> dict:
        """Import the relational eval CSV set in FK-safe order, atomically."""
        supplied={name.split("/")[-1]:text for name,text in files.items()}
        unknown=sorted(set(supplied)-set(self.DATASET_FILES)-{"16_import_order.csv","17_dataset_summary.csv","18_dataset_metadata.csv"})
        if unknown: raise BookingError("INVALID_INPUT",f"File không được hỗ trợ: {', '.join(unknown)}")
        counts={}; skipped=[]
        with self.db.transaction(immediate=True) as c:
            for filename,(table,expected) in self.DATASET_FILES.items():
                if filename not in supplied: continue
                reader=csv.DictReader(io.StringIO(supplied[filename].lstrip("\ufeff")))
                if reader.fieldnames != expected:
                    raise BookingError("INVALID_INPUT",f"Header {filename} không đúng. Cần: {','.join(expected)}")
                rows=list(reader)
                if not rows: counts[table]=0; continue
                self._assert_dataset_references(c,filename,rows,self.DATASET_REFERENCES.get(filename,()))
                insert_columns=list(expected)
                if filename=="14_booking_access_sessions.csv": insert_columns.insert(1,"token_hash")
                marks=",".join("?"*len(insert_columns)); updates=",".join(f"{col}=excluded.{col}" for col in insert_columns if col!="id" and col!="booking_id")
                conflict="booking_id" if "booking_id" in insert_columns and "id" not in insert_columns else "id"
                sql=f"INSERT INTO {table}({','.join(insert_columns)}) VALUES({marks}) ON CONFLICT({conflict}) DO UPDATE SET {updates}"
                try:
                    for row in rows:
                        values=[None if row[col]=="" else row[col] for col in expected]
                        if filename=="14_booking_access_sessions.csv": values.insert(1,self._hash(row["id"],"mock-session"))
                        c.execute(sql,values)
                except sqlite3.IntegrityError as exc:
                    raise BookingError("INVALID_INPUT",f"Không thể import {filename}: thiếu dữ liệu phụ thuộc hoặc vi phạm constraint ({exc}).") from exc
                counts[table]=len(rows)
        return {"imported":counts,"total_rows":sum(counts.values()),"skipped":skipped,"missing_expected_files":[name for name in self.DATASET_FILES if name not in supplied]}

    def expire_held_bookings(self) -> int:
        count=0
        with self.db.transaction(immediate=True) as c:
            for b in c.execute("SELECT * FROM bookings WHERE status='held' AND hold_expires_at<=?",(iso(self.now()),)).fetchall():
                c.execute("UPDATE bookings SET status='expired',version=version+1,updated_at=? WHERE id=? AND status='held'",(iso(self.now()),b["id"])); c.execute("UPDATE test_drive_slots SET status='available',held_until=NULL,current_booking_id=NULL,updated_at=? WHERE id=? AND current_booking_id=?",(iso(self.now()),b["slot_id"],b["id"])); self._event(c,b["id"],"hold_expired"); count+=1
        return count

    def get_dashboard(self, limit: int = 50) -> dict:
        """Return a read-only operational snapshot without OTP or raw license data."""
        with self.db.connect() as c:
            booking_counts={r["status"]:r["count"] for r in c.execute("SELECT status,count(*) count FROM bookings GROUP BY status")}
            slot_counts={r["status"]:r["count"] for r in c.execute("SELECT status,count(*) count FROM test_drive_slots GROUP BY status")}
            rows=c.execute("""SELECT b.id,b.booking_code,b.status,b.source_channel,b.version,b.created_at,b.updated_at,
                s.start_at,s.end_at,sh.name showroom_name,m.name vehicle_model,v.name vehicle_variant,
                bp.full_name booker_name,dp.full_name driver_name
                FROM bookings b JOIN test_drive_slots s ON s.id=b.slot_id
                JOIN showrooms sh ON sh.id=s.showroom_id JOIN demo_vehicles d ON d.id=s.demo_vehicle_id
                JOIN vehicle_variants v ON v.id=d.variant_id JOIN vehicle_models m ON m.id=v.model_id
                LEFT JOIN people bp ON bp.id=b.booker_person_id LEFT JOIN people dp ON dp.id=b.driver_person_id
                ORDER BY b.updated_at DESC LIMIT ?""",(min(max(limit,1),200),)).fetchall()
            pending_jobs=c.execute("SELECT count(*) FROM notification_jobs WHERE status IN ('pending','processing')").fetchone()[0]
            active_holds=c.execute("SELECT count(*) FROM bookings WHERE status='held' AND hold_expires_at>?",(iso(self.now()),)).fetchone()[0]
        return {"booking_counts":booking_counts,"slot_counts":slot_counts,"active_holds":active_holds,"pending_notification_jobs":pending_jobs,"recent_bookings":[dict(r) for r in rows],"generated_at":iso(self.now())}
