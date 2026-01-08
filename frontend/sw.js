// HopeLink Service Worker - PWA 오프라인 지원
const CACHE_NAME = 'hopelink-v1';
const urlsToCache = [
    './',
    './index.html',
    './manifest.json'
];

// 설치 시 캐시
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
    self.skipWaiting();
});

// 네트워크 요청 처리
self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => {
                // 캐시에 있으면 캐시 반환, 없으면 네트워크 요청
                return response || fetch(event.request);
            })
            .catch(() => {
                // 오프라인일 때 기본 페이지 반환
                if (event.request.mode === 'navigate') {
                    return caches.match('./index.html');
                }
            })
    );
});

// 캐시 업데이트
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});
