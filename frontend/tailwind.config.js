    /** @type {import('tailwindcss').Config} */
    module.exports = {
      content: [
        "./src/**/*.{js,jsx,ts,tsx}", // THIS IS CRUCIAL: It tells Tailwind to scan your source files for classes.
      ],
      theme: {
        extend: {},
      },
      plugins: [],
    }
    