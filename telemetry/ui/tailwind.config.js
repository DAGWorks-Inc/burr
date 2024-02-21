/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        dwdarkblue: "rgb(43,49,82)",
        dwred: "rgb(234,85,86)",
        dwlightblue: "rgb(66,157,188)",
        dwwhite: "white",
        dwblack: "black",
    },},
  },
  // Only use this for debugging!
  plugins: [
    require("tailwindcss-question-mark"),
  ],
};
