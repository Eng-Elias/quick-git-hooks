// eslint.config.js
// Default configuration provided by quick-git-hooks
// Customize this file to your project's needs.

// Global ignores - customize these patterns as needed
export default [
  {
    ignores: [
      // Add files/directories to ignore here:
      "**/dist/*",
      "**/build/*",
      "**/*.*.min.*",
      "**/*.config.js",
    ],
  },
  {
    // Apply to JS/TS/JSX/TSX files
    files: ["**/*.{js,mjs,cjs,jsx,ts,mts,tsx}"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      parserOptions: {
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    linterOptions: {
      reportUnusedDisableDirectives: true,
    },
    rules: {
      // Essential rules
      "no-unused-vars": "warn",
      "no-undef": "error",
      "no-console": "warn",
      "no-debugger": "warn",

      // Best practices
      eqeqeq: ["error", "always"],
      "no-var": "error",
      "prefer-const": "warn",
      "no-multiple-empty-lines": ["warn", { max: 1 }],
      "no-trailing-spaces": "warn",
      semi: ["error", "always"],
      quotes: ["error", "single", { avoidEscape: true }],
      indent: ["error", 2],

      // Modern JavaScript
      "arrow-body-style": ["error", "as-needed"],
      "object-shorthand": ["warn", "always"],
      "prefer-template": "warn",
      "prefer-destructuring": [
        "warn",
        {
          array: false,
          object: true,
        },
      ],
    },
  },
  // TypeScript-specific rules (if TS files are detected)
  {
    files: ["**/*.{ts,tsx,mts}"],
    languageOptions: {
      parser: "@typescript-eslint/parser",
      parserOptions: {
        project: "./tsconfig.json", // Will be used if exists
      },
    },
    rules: {
      // TypeScript rules here
      "@typescript-eslint/explicit-function-return-type": "off",
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-unused-vars": [
        "warn",
        {
          argsIgnorePattern: "^_",
          varsIgnorePattern: "^_",
        },
      ],
    },
  },
];
