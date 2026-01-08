-- =====================================================
-- HopeLink 희귀질환 케어 앱 - Supabase 데이터베이스 스키마
-- =====================================================

-- 1. 사용자 테이블 (Users)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    profile_image_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 환아 정보 테이블 (Children)
CREATE TABLE children (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    birth_date DATE NOT NULL,
    disease_code VARCHAR(20) NOT NULL,  -- ICD-10 질병 코드
    disease_name VARCHAR(200),
    symptoms TEXT[],  -- 주요 증상 배열
    current_hospital VARCHAR(200),
    attending_doctor VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 관찰 일기 테이블 (Observation Diaries) - 모듈 A
CREATE TABLE observation_diaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID REFERENCES children(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    video_url TEXT,
    thumbnail_url TEXT,
    duration_seconds INTEGER,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- AI 분석 결과
    ai_analysis JSONB,  -- {spasm_count, occurrence_times, patterns, severity}
    spasm_count INTEGER,
    occurrence_times TIMESTAMP WITH TIME ZONE[],
    symptom_tags TEXT[],
    
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 4. AI 의사 보고서 테이블 (AI Reports) - 모듈 A
CREATE TABLE ai_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID REFERENCES children(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    report_type VARCHAR(50) NOT NULL,  -- 'weekly', 'monthly', 'custom'
    date_range_start DATE NOT NULL,
    date_range_end DATE NOT NULL,
    
    -- 보고서 내용
    summary TEXT NOT NULL,
    symptom_frequency JSONB,  -- 증상별 빈도 통계
    trend_analysis TEXT,
    recommendations TEXT[],
    
    pdf_url TEXT,
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 5. 케어 일정 테이블 (Care Schedules) - 모듈 C, E
CREATE TABLE care_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID REFERENCES children(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    title VARCHAR(200) NOT NULL,
    schedule_type VARCHAR(50) NOT NULL,  -- 'hospital', 'rehabilitation', 'therapy', 'checkup'
    
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    is_all_day BOOLEAN DEFAULT FALSE,
    
    -- 병원/센터 정보
    location_name VARCHAR(200),
    location_address TEXT,
    department VARCHAR(100),
    doctor_name VARCHAR(100),
    
    -- 준비물 체크리스트
    checklist JSONB,  -- [{item: "의료보험증", checked: false}, ...]
    
    -- Google Calendar 동기화
    google_event_id VARCHAR(255),
    is_synced BOOLEAN DEFAULT FALSE,
    
    -- 충돌 감지
    has_conflict BOOLEAN DEFAULT FALSE,
    conflict_with UUID[],  -- 충돌하는 다른 일정 ID들
    
    reminder_minutes INTEGER[] DEFAULT ARRAY[1440, 60],  -- 기본: 1일 전, 1시간 전
    notes TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 6. Google Calendar 동기화 설정 테이블 (Calendar Sync) - 모듈 E
CREATE TABLE calendar_sync_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    
    google_account_email VARCHAR(255),
    google_refresh_token TEXT,
    google_calendar_id VARCHAR(255),
    
    is_enabled BOOLEAN DEFAULT TRUE,
    sync_direction VARCHAR(20) DEFAULT 'bidirectional',  -- 'to_google', 'from_google', 'bidirectional'
    last_synced_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 7. 병원 추천 테이블 (Hospital Recommendations) - 모듈 C, D
CREATE TABLE hospital_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_id UUID REFERENCES children(id) ON DELETE CASCADE,
    
    hospital_name VARCHAR(200) NOT NULL,
    hospital_type VARCHAR(50),  -- 'tertiary', 'rehabilitation', 'specialized'
    address TEXT,
    phone VARCHAR(50),
    website_url TEXT,
    
    -- 매칭 점수
    match_score DECIMAL(3,2),  -- 0.00 ~ 1.00
    match_reasons TEXT[],
    
    -- 전문의 정보
    specialist_name VARCHAR(100),
    specialist_specialty VARCHAR(100),
    
    -- 대기 정보 (모듈 D)
    avg_wait_days INTEGER,
    cancellation_pattern JSONB,  -- {golden_hours: [...], peak_days: [...]}
    
    -- 예약 팁
    booking_tips TEXT[],
    required_documents TEXT[],
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 8. 취소분 알림 테이블 (Waiting Radar) - 모듈 D
CREATE TABLE cancellation_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    child_id UUID REFERENCES children(id) ON DELETE CASCADE,
    
    hospital_name VARCHAR(200) NOT NULL,
    department VARCHAR(100),
    doctor_name VARCHAR(100),
    
    -- 감시 설정
    is_watching BOOLEAN DEFAULT TRUE,
    preferred_dates DATE[],
    preferred_time_slots VARCHAR(20)[],  -- 'morning', 'afternoon', 'evening'
    
    -- 알림 이력
    last_alert_at TIMESTAMP WITH TIME ZONE,
    alert_count INTEGER DEFAULT 0,
    
    -- 원무과 연결 정보
    hospital_phone VARCHAR(50),
    reservation_url TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 9. 글로벌 연구 브리핑 테이블 (Research Briefings) - 모듈 F
CREATE TABLE research_briefings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    title VARCHAR(500) NOT NULL,
    source VARCHAR(100) NOT NULL,  -- 'FDA', 'EMA', 'Lancet', 'NEJM', etc.
    source_url TEXT,
    
    disease_codes VARCHAR(20)[],  -- 관련 질병 코드들
    
    briefing_type VARCHAR(50),  -- 'approval', 'clinical_trial', 'research_paper'
    phase VARCHAR(20),  -- 'phase1', 'phase2', 'phase3', 'approved'
    
    summary_korean TEXT NOT NULL,
    summary_english TEXT,
    key_findings TEXT[],
    
    published_date DATE,
    briefed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 10. 가족 연결 테이블 (Hope-Connector) - 모듈 G
CREATE TABLE family_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    matched_user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- 매칭 기준
    disease_code VARCHAR(20),
    symptom_similarity DECIMAL(3,2),
    
    -- 연결 상태
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'accepted', 'declined', 'blocked'
    
    -- 익명 채팅방
    chat_room_id UUID,
    is_anonymous BOOLEAN DEFAULT TRUE,
    
    connected_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 11. 행정 서류 테이블 (Admin Automation) - 모듈 H
CREATE TABLE admin_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    child_id UUID REFERENCES children(id) ON DELETE CASCADE,
    
    document_type VARCHAR(100) NOT NULL,  -- 'sanjeong_teukrye', 'medical_expense', 'disability_registration'
    document_name VARCHAR(200) NOT NULL,
    
    -- 자동 완성 데이터
    form_data JSONB,
    
    -- 생성된 PDF
    pdf_url TEXT,
    
    -- 상태
    status VARCHAR(20) DEFAULT 'draft',  -- 'draft', 'completed', 'submitted'
    submitted_at TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 12. 챗봇 대화 기록 테이블 (Intelligence Assistant) - 모듈 B
CREATE TABLE chat_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    session_id UUID NOT NULL,
    
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant'
    content TEXT NOT NULL,
    
    -- 첨부 파일 (의료 문서 등)
    attachments JSONB,  -- [{type: 'medical_record', url: '...', translated_text: '...'}]
    
    -- AI 분석 메타데이터
    intent VARCHAR(100),  -- 'welfare_inquiry', 'medical_info', 'hospital_search'
    confidence DECIMAL(3,2),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX idx_children_user_id ON children(user_id);
CREATE INDEX idx_children_disease_code ON children(disease_code);
CREATE INDEX idx_observation_diaries_child_id ON observation_diaries(child_id);
CREATE INDEX idx_care_schedules_child_id ON care_schedules(child_id);
CREATE INDEX idx_care_schedules_start_time ON care_schedules(start_time);
CREATE INDEX idx_research_briefings_disease_codes ON research_briefings USING GIN(disease_codes);
CREATE INDEX idx_family_connections_disease_code ON family_connections(disease_code);
CREATE INDEX idx_chat_conversations_session_id ON chat_conversations(session_id);

-- Row Level Security (RLS) 정책
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE children ENABLE ROW LEVEL SECURITY;
ALTER TABLE observation_diaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE care_schedules ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_sync_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE cancellation_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_conversations ENABLE ROW LEVEL SECURITY;

-- 사용자 본인 데이터만 접근 가능하도록 정책 설정
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Users can manage own children" ON children
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own diaries" ON observation_diaries
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own reports" ON ai_reports
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own schedules" ON care_schedules
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own calendar settings" ON calendar_sync_settings
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own alerts" ON cancellation_alerts
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own documents" ON admin_documents
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can view own chats" ON chat_conversations
    FOR ALL USING (auth.uid() = user_id);
