/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./**/*.{html,js}"],
  theme: {
    extend: {
      // HopeLink 파스텔 톤 컬러 팔레트
      colors: {
        // Primary - 소프트 핑크 (따뜻함, 사랑)
        primary: {
          50: '#FFF5F6',
          100: '#FFE8EA',
          200: '#FFD4D8',
          300: '#FFB5BA',
          400: '#FF9AA1',
          500: '#FF7A84',
          600: '#E85A65',
          DEFAULT: '#FFB5BA',
        },
        // Secondary - 라벤더 (안정, 평화)
        secondary: {
          50: '#FAF5FA',
          100: '#F3E8F3',
          200: '#E8D5E8',
          300: '#D8BDD8',
          400: '#C9A5C9',
          500: '#B88DB8',
          DEFAULT: '#E8D5E8',
        },
        // Accent - 민트 (희망, 치유)
        accent: {
          50: '#F0FBF7',
          100: '#D9F5EB',
          200: '#B8E8D4',
          300: '#8DD9BC',
          400: '#62CAA4',
          500: '#3BBB8C',
          DEFAULT: '#B8E8D4',
        },
        // Background - 크림 (안락함)
        cream: {
          50: '#FFFDFB',
          100: '#FFF9F0',
          200: '#FFF5E6',
          DEFAULT: '#FFF9F0',
        },
        // 상태 컬러
        warning: {
          light: '#FFF3CD',
          DEFAULT: '#FFD93D',
          dark: '#CC9A00',
        },
        danger: {
          light: '#FFE5E5',
          DEFAULT: '#FF6B6B',
          dark: '#CC3333',
        },
        success: {
          light: '#E8F5E9',
          DEFAULT: '#4CAF50',
          dark: '#2E7D32',
        },
        // 중립 컬러
        neutral: {
          50: '#FAFAFA',
          100: '#F5F5F5',
          200: '#EEEEEE',
          300: '#E0E0E0',
          400: '#BDBDBD',
          500: '#9E9E9E',
          600: '#757575',
          700: '#616161',
          800: '#424242',
          900: '#212121',
        },
      },
      // 그림자
      boxShadow: {
        'soft': '0 2px 8px rgba(255, 181, 186, 0.15)',
        'soft-lg': '0 4px 16px rgba(255, 181, 186, 0.2)',
        'card': '0 4px 20px rgba(0, 0, 0, 0.05)',
        'card-hover': '0 8px 30px rgba(255, 181, 186, 0.25)',
        'floating': '0 10px 40px rgba(255, 122, 132, 0.3)',
      },
      // 폰트
      fontFamily: {
        sans: ['Pretendard', 'Noto Sans KR', 'sans-serif'],
      },
      // 라운드
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
      },
      // 애니메이션
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
        'pulse-soft': 'pulseSoft 2s infinite',
        'bounce-soft': 'bounceSoft 1s infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        bounceSoft: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-5px)' },
        },
      },
    },
  },
  plugins: [],
}
