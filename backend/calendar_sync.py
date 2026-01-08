"""
HopeLink - Google Calendar 연동 및 일정 충돌 감지 모듈
=====================================================

기능:
- Google Calendar API OAuth2 인증
- 양방향 일정 동기화 (HopeLink ↔ Google Calendar)
- 일정 충돌(시간 겹침) 감지 및 경고
- 진료 전날 준비물 리마인더 생성
"""

import os
from datetime import datetime, timedelta
from typing import Optional
from dataclasses import dataclass, field
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import pickle

# Google Calendar API 권한 범위
SCOPES = ['https://www.googleapis.com/auth/calendar']


@dataclass
class Schedule:
    """케어 일정 데이터 클래스"""
    id: str
    title: str
    schedule_type: str  # 'hospital', 'rehabilitation', 'therapy', 'checkup'
    start_time: datetime
    end_time: datetime
    location_name: Optional[str] = None
    location_address: Optional[str] = None
    department: Optional[str] = None
    doctor_name: Optional[str] = None
    checklist: list = field(default_factory=list)
    notes: Optional[str] = None
    google_event_id: Optional[str] = None


@dataclass
class ScheduleConflict:
    """일정 충돌 정보"""
    schedule_a: Schedule
    schedule_b: Schedule
    overlap_start: datetime
    overlap_end: datetime
    overlap_minutes: int
    conflict_type: str  # 'full_overlap', 'partial_overlap', 'contains'
    
    def to_dict(self) -> dict:
        return {
            'schedule_a_id': self.schedule_a.id,
            'schedule_a_title': self.schedule_a.title,
            'schedule_b_id': self.schedule_b.id,
            'schedule_b_title': self.schedule_b.title,
            'overlap_start': self.overlap_start.isoformat(),
            'overlap_end': self.overlap_end.isoformat(),
            'overlap_minutes': self.overlap_minutes,
            'conflict_type': self.conflict_type,
            'warning_message': self._generate_warning()
        }
    
    def _generate_warning(self) -> str:
        """사용자 친화적 경고 메시지 생성"""
        time_str = self.overlap_start.strftime('%Y-%m-%d %H:%M')
        return (
            f"⚠️ 일정 충돌 감지: '{self.schedule_a.title}'과(와) "
            f"'{self.schedule_b.title}'이(가) {time_str}에 "
            f"{self.overlap_minutes}분간 겹칩니다."
        )


@dataclass
class Reminder:
    """준비물 리마인더"""
    schedule: Schedule
    reminder_time: datetime
    checklist_items: list
    message: str


class GoogleCalendarSync:
    """Google Calendar 양방향 동기화 클래스"""
    
    def __init__(self, credentials_path: str = 'credentials.json', token_path: str = 'token.pickle'):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.creds = None
        self.service = None
    
    def authenticate(self) -> bool:
        """Google OAuth2 인증 수행"""
        try:
            # 저장된 토큰 확인
            if os.path.exists(self.token_path):
                with open(self.token_path, 'rb') as token:
                    self.creds = pickle.load(token)
            
            # 토큰이 없거나 만료된 경우
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_path):
                        raise FileNotFoundError(
                            f"Google API credentials 파일을 찾을 수 없습니다: {self.credentials_path}\n"
                            "Google Cloud Console에서 OAuth 2.0 클라이언트 ID를 생성하세요."
                        )
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                
                # 토큰 저장
                with open(self.token_path, 'wb') as token:
                    pickle.dump(self.creds, token)
            
            self.service = build('calendar', 'v3', credentials=self.creds)
            return True
            
        except Exception as e:
            print(f"인증 실패: {e}")
            return False
    
    def get_events(
        self, 
        calendar_id: str = 'primary',
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 100
    ) -> list[dict]:
        """Google Calendar에서 이벤트 가져오기"""
        if not self.service:
            raise RuntimeError("먼저 authenticate()를 호출하세요.")
        
        if time_min is None:
            time_min = datetime.utcnow()
        if time_max is None:
            time_max = time_min + timedelta(days=30)
        
        try:
            events_result = self.service.events().list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat() + 'Z',
                timeMax=time_max.isoformat() + 'Z',
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
            
        except HttpError as e:
            print(f"이벤트 조회 실패: {e}")
            return []
    
    def create_event(
        self,
        schedule: Schedule,
        calendar_id: str = 'primary'
    ) -> Optional[str]:
        """HopeLink 일정을 Google Calendar에 추가"""
        if not self.service:
            raise RuntimeError("먼저 authenticate()를 호출하세요.")
        
        event = {
            'summary': f"[HopeLink] {schedule.title}",
            'description': self._build_event_description(schedule),
            'start': {
                'dateTime': schedule.start_time.isoformat(),
                'timeZone': 'Asia/Seoul',
            },
            'end': {
                'dateTime': schedule.end_time.isoformat(),
                'timeZone': 'Asia/Seoul',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 1440},  # 1일 전
                    {'method': 'popup', 'minutes': 60},    # 1시간 전
                ],
            },
        }
        
        if schedule.location_address:
            event['location'] = schedule.location_address
        
        try:
            created_event = self.service.events().insert(
                calendarId=calendar_id,
                body=event
            ).execute()
            
            return created_event.get('id')
            
        except HttpError as e:
            print(f"이벤트 생성 실패: {e}")
            return None
    
    def update_event(
        self,
        schedule: Schedule,
        calendar_id: str = 'primary'
    ) -> bool:
        """Google Calendar 이벤트 업데이트"""
        if not self.service or not schedule.google_event_id:
            return False
        
        event = {
            'summary': f"[HopeLink] {schedule.title}",
            'description': self._build_event_description(schedule),
            'start': {
                'dateTime': schedule.start_time.isoformat(),
                'timeZone': 'Asia/Seoul',
            },
            'end': {
                'dateTime': schedule.end_time.isoformat(),
                'timeZone': 'Asia/Seoul',
            },
        }
        
        if schedule.location_address:
            event['location'] = schedule.location_address
        
        try:
            self.service.events().update(
                calendarId=calendar_id,
                eventId=schedule.google_event_id,
                body=event
            ).execute()
            return True
            
        except HttpError as e:
            print(f"이벤트 업데이트 실패: {e}")
            return False
    
    def delete_event(
        self,
        google_event_id: str,
        calendar_id: str = 'primary'
    ) -> bool:
        """Google Calendar 이벤트 삭제"""
        if not self.service:
            return False
        
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=google_event_id
            ).execute()
            return True
            
        except HttpError as e:
            print(f"이벤트 삭제 실패: {e}")
            return False
    
    def _build_event_description(self, schedule: Schedule) -> str:
        """이벤트 설명 문자열 생성"""
        lines = [f"📋 일정 유형: {schedule.schedule_type}"]
        
        if schedule.location_name:
            lines.append(f"🏥 장소: {schedule.location_name}")
        if schedule.department:
            lines.append(f"🩺 진료과: {schedule.department}")
        if schedule.doctor_name:
            lines.append(f"👨‍⚕️ 담당의: {schedule.doctor_name}")
        
        if schedule.checklist:
            lines.append("\n✅ 준비물 체크리스트:")
            for item in schedule.checklist:
                checked = "☑️" if item.get('checked', False) else "⬜"
                lines.append(f"  {checked} {item.get('item', '')}")
        
        if schedule.notes:
            lines.append(f"\n📝 메모: {schedule.notes}")
        
        lines.append("\n---\n이 일정은 HopeLink 앱에서 생성되었습니다.")
        
        return "\n".join(lines)


def detect_schedule_conflicts(schedules: list[Schedule]) -> list[ScheduleConflict]:
    """
    일정 목록에서 시간이 겹치는 충돌을 감지합니다.
    
    Args:
        schedules: 검사할 일정 목록
        
    Returns:
        감지된 충돌 목록
    """
    conflicts = []
    n = len(schedules)
    
    # 시작 시간 순으로 정렬
    sorted_schedules = sorted(schedules, key=lambda s: s.start_time)
    
    for i in range(n):
        for j in range(i + 1, n):
            schedule_a = sorted_schedules[i]
            schedule_b = sorted_schedules[j]
            
            # 충돌 여부 확인
            conflict = _check_overlap(schedule_a, schedule_b)
            if conflict:
                conflicts.append(conflict)
    
    return conflicts


def _check_overlap(a: Schedule, b: Schedule) -> Optional[ScheduleConflict]:
    """두 일정 간의 시간 겹침을 확인합니다."""
    # 겹치지 않는 경우
    if a.end_time <= b.start_time or b.end_time <= a.start_time:
        return None
    
    # 겹치는 구간 계산
    overlap_start = max(a.start_time, b.start_time)
    overlap_end = min(a.end_time, b.end_time)
    overlap_minutes = int((overlap_end - overlap_start).total_seconds() / 60)
    
    # 충돌 유형 결정
    if a.start_time == b.start_time and a.end_time == b.end_time:
        conflict_type = 'full_overlap'
    elif a.start_time <= b.start_time and a.end_time >= b.end_time:
        conflict_type = 'contains'
    elif b.start_time <= a.start_time and b.end_time >= a.end_time:
        conflict_type = 'contains'
    else:
        conflict_type = 'partial_overlap'
    
    return ScheduleConflict(
        schedule_a=a,
        schedule_b=b,
        overlap_start=overlap_start,
        overlap_end=overlap_end,
        overlap_minutes=overlap_minutes,
        conflict_type=conflict_type
    )


def sync_to_google_calendar(
    schedule: Schedule,
    calendar_sync: GoogleCalendarSync
) -> tuple[bool, Optional[str]]:
    """
    HopeLink 일정을 Google Calendar에 동기화합니다.
    
    Args:
        schedule: 동기화할 일정
        calendar_sync: 인증된 GoogleCalendarSync 인스턴스
        
    Returns:
        (성공 여부, Google Event ID 또는 에러 메시지)
    """
    try:
        if schedule.google_event_id:
            # 기존 이벤트 업데이트
            success = calendar_sync.update_event(schedule)
            if success:
                return (True, schedule.google_event_id)
            return (False, "이벤트 업데이트 실패")
        else:
            # 새 이벤트 생성
            event_id = calendar_sync.create_event(schedule)
            if event_id:
                return (True, event_id)
            return (False, "이벤트 생성 실패")
            
    except Exception as e:
        return (False, str(e))


def create_reminder_with_checklist(
    schedule: Schedule,
    reminder_hours_before: int = 24
) -> Reminder:
    """
    진료 전날 준비물이 포함된 리마인더를 생성합니다.
    
    Args:
        schedule: 대상 일정
        reminder_hours_before: 리마인더 발송 시간 (일정 시작 전 시간)
        
    Returns:
        생성된 리마인더 객체
    """
    reminder_time = schedule.start_time - timedelta(hours=reminder_hours_before)
    
    # 진료과별 기본 준비물
    default_checklists = {
        'hospital': [
            {'item': '신분증', 'checked': False},
            {'item': '건강보험증', 'checked': False},
            {'item': '진료의뢰서 (있는 경우)', 'checked': False},
            {'item': '이전 검사 결과지', 'checked': False},
            {'item': '복용 중인 약 목록', 'checked': False},
        ],
        'rehabilitation': [
            {'item': '편한 운동복', 'checked': False},
            {'item': '실내화', 'checked': False},
            {'item': '재활 일지', 'checked': False},
            {'item': '보조기구 (있는 경우)', 'checked': False},
        ],
        'therapy': [
            {'item': '치료 기록지', 'checked': False},
            {'item': '관찰 일기', 'checked': False},
            {'item': '아이가 좋아하는 장난감', 'checked': False},
        ],
        'checkup': [
            {'item': '금식 여부 확인', 'checked': False},
            {'item': '이전 검진 결과지', 'checked': False},
            {'item': '산정특례 확인서', 'checked': False},
        ],
    }
    
    # 사용자 정의 체크리스트 + 기본 체크리스트 병합
    checklist_items = schedule.checklist.copy() if schedule.checklist else []
    default_items = default_checklists.get(schedule.schedule_type, [])
    
    for default_item in default_items:
        if not any(item.get('item') == default_item['item'] for item in checklist_items):
            checklist_items.append(default_item)
    
    # 리마인더 메시지 생성
    date_str = schedule.start_time.strftime('%m월 %d일 %H시 %M분')
    location = schedule.location_name or '예정된 장소'
    
    message_lines = [
        f"📅 내일 일정 알림",
        f"",
        f"'{schedule.title}'",
        f"📍 {location}",
        f"⏰ {date_str}",
        f"",
        f"✅ 준비물을 확인하세요:",
    ]
    
    for item in checklist_items:
        message_lines.append(f"  • {item.get('item', '')}")
    
    return Reminder(
        schedule=schedule,
        reminder_time=reminder_time,
        checklist_items=checklist_items,
        message="\n".join(message_lines)
    )


# =====================================================
# 사용 예시
# =====================================================

if __name__ == "__main__":
    # 1. 테스트 일정 생성
    schedules = [
        Schedule(
            id="schedule_1",
            title="서울대병원 신경과 진료",
            schedule_type="hospital",
            start_time=datetime(2026, 1, 10, 14, 0),
            end_time=datetime(2026, 1, 10, 15, 30),
            location_name="서울대학교병원",
            location_address="서울특별시 종로구 대학로 101",
            department="소아신경과",
            doctor_name="김OO 교수",
            checklist=[
                {'item': 'MRI 결과지', 'checked': False},
                {'item': '관찰 일기 영상', 'checked': False},
            ]
        ),
        Schedule(
            id="schedule_2",
            title="재활치료",
            schedule_type="rehabilitation",
            start_time=datetime(2026, 1, 10, 15, 0),  # 진료와 30분 겹침!
            end_time=datetime(2026, 1, 10, 16, 0),
            location_name="어린이재활센터"
        ),
        Schedule(
            id="schedule_3",
            title="언어치료",
            schedule_type="therapy",
            start_time=datetime(2026, 1, 10, 17, 0),
            end_time=datetime(2026, 1, 10, 18, 0),
            location_name="○○언어치료실"
        ),
    ]
    
    # 2. 충돌 감지 테스트
    print("=" * 50)
    print("🔍 일정 충돌 감지 테스트")
    print("=" * 50)
    
    conflicts = detect_schedule_conflicts(schedules)
    
    if conflicts:
        print(f"\n⚠️ {len(conflicts)}개의 충돌이 감지되었습니다:\n")
        for conflict in conflicts:
            print(conflict.to_dict()['warning_message'])
            print(f"   - 충돌 유형: {conflict.conflict_type}")
            print(f"   - 겹치는 시간: {conflict.overlap_minutes}분")
            print()
    else:
        print("\n✅ 충돌이 없습니다.")
    
    # 3. 리마인더 생성 테스트
    print("\n" + "=" * 50)
    print("📋 준비물 리마인더 테스트")
    print("=" * 50)
    
    reminder = create_reminder_with_checklist(schedules[0])
    print(f"\n리마인더 발송 시간: {reminder.reminder_time}")
    print("\n" + reminder.message)
    
    # 4. Google Calendar 연동 테스트 (credentials.json 필요)
    print("\n" + "=" * 50)
    print("🔄 Google Calendar 동기화")
    print("=" * 50)
    
    print("\n📌 Google Calendar 연동을 위해서는:")
    print("   1. Google Cloud Console에서 프로젝트 생성")
    print("   2. Calendar API 활성화")
    print("   3. OAuth 2.0 클라이언트 ID 생성")
    print("   4. credentials.json 파일을 이 디렉토리에 저장")
    print("\n   자세한 가이드: https://developers.google.com/calendar/quickstart/python")
