# HopeLink 앱 배포 가이드

## 🚀 배포 옵션

### 1. Vercel + Supabase (추천 - 무료)

가장 간단하고 무료로 사용 가능한 조합입니다.

#### 준비물
- GitHub 계정
- Vercel 계정 (GitHub로 로그인)
- Supabase 계정 (무료)

#### 배포 단계

**Step 1: GitHub에 코드 업로드**
```bash
cd "c:\Users\hi740\OneDrive\바탕 화면\호프링크"
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/hopelink.git
git push -u origin main
```

**Step 2: Supabase 프로젝트 생성**
1. https://supabase.com 접속 → 회원가입
2. "New Project" 클릭
3. 프로젝트 이름: `hopelink`
4. 데이터베이스 비밀번호 설정
5. Region: `Northeast Asia (Seoul)` 선택
6. 생성 후 Settings → API에서 URL과 anon key 복사

**Step 3: 데이터베이스 테이블 생성**
- Supabase → SQL Editor
- `database/schema.sql` 내용 붙여넣기 → Run

**Step 4: Vercel 배포**
1. https://vercel.com 접속 → GitHub로 로그인
2. "Import Project" → GitHub 저장소 선택
3. Framework: `Other`
4. Root Directory: `backend`
5. Build Command: `pip install -r requirements.txt`
6. Output Directory: (비우기)
7. Environment Variables 추가:
   - `SUPABASE_URL`: (Supabase URL)
   - `SUPABASE_ANON_KEY`: (Supabase Key)
   - `JWT_SECRET_KEY`: (랜덤 문자열)

**Step 5: 프론트엔드 배포**
백엔드와 별도로 프론트엔드를 Vercel에 배포하거나,
백엔드에서 정적 파일 제공 (현재 구현됨)

---

### 2. Railway (간편한 백엔드 배포)

Railway는 Python 백엔드 배포에 특화되어 있습니다.

1. https://railway.app 접속
2. GitHub 연결 → 저장소 선택
3. Environment Variables 설정
4. 자동 배포 완료!

---

### 3. 직접 서버 운영

VPS (Virtual Private Server)를 사용하는 방법:

1. AWS, GCP, Azure 등에서 서버 생성
2. Python, Nginx 설치
3. FastAPI를 Gunicorn으로 실행
4. Nginx로 리버스 프록시 설정
5. SSL 인증서 (Let's Encrypt) 설정

---

## 📱 모바일 앱 배포

### PWA (현재 구현됨)
- 웹 배포 후 휴대폰에서 "홈 화면에 추가"
- 앱스토어 없이 앱처럼 사용 가능

### 네이티브 앱 (추가 개발 필요)
- React Native 또는 Flutter로 변환
- iOS: App Store 등록 (연 $99)
- Android: Play Store 등록 (1회 $25)

---

## ⚠️ 프로덕션 체크리스트

- [ ] JWT_SECRET_KEY를 안전한 랜덤 문자열로 변경
- [ ] CORS origin을 실제 도메인으로 제한
- [ ] HTTPS 적용 (Vercel/Railway는 자동 적용)
- [ ] Supabase Row Level Security(RLS) 활성화
- [ ] 에러 로깅 설정 (Sentry 등)
- [ ] 백업 정책 수립
