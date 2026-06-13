/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        lf: {
          bg:        '#ffffff',
          bg2:       '#faf8f4',
          bg3:       '#f4f0e8',
          navy:      '#12100e',
          body:      '#3d3830',
          mid:       '#7c756e',
          muted:     '#b8b0a8',
          gold:      '#9a7840',
          'gold-lt': '#b8935a',
        },
      },
      fontFamily: {
        serif: ['"DM Serif Display"', '"Noto Serif KR"', 'Georgia', 'serif'],
        sans:  ['"Noto Sans KR"', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
