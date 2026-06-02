/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172026",
        panel: "#f7f8f7",
        steel: "#d6dddc",
        signal: "#146b63",
        caution: "#c68614",
        danger: "#b5413c",
      },
    },
  },
  plugins: [],
};
