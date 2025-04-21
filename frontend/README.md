# Financial Symbol Lookup - Frontend

This is the frontend application for the Financial Symbol Lookup project, built with [Next.js](https://nextjs.org) and TypeScript.

## Tech Stack

- [Next.js 14](https://nextjs.org) - React framework for production
- [TypeScript](https://www.typescriptlang.org) - Type-safe JavaScript
- [Geist Font](https://vercel.com/font) - Modern, clean font family
- [Tailwind CSS](https://tailwindcss.com) - Utility-first CSS framework

## Getting Started

### Prerequisites

- Node.js 18.17 or later
- npm, yarn, or pnpm

### Installation

1. Install dependencies:
```bash
npm install
# or
yarn install
# or
pnpm install
```

2. Run the development server:
```bash
npm run dev
# or
yarn dev
# or
pnpm dev
```

3. Open [http://localhost:3000](http://localhost:3000) with your browser to see the application.

## Project Structure

- `src/app/` - Next.js App Router pages and components
- `src/components/` - Reusable React components
- `public/` - Static assets including favicons and images

## Development

- The main application page is located at `src/app/page.tsx`
- Global styles are defined in `src/app/globals.css`
- Layout and metadata configuration is in `src/app/layout.tsx`

## Features

- Financial symbol search and lookup
- Responsive design for all devices
- Modern UI with Geist font and Tailwind CSS
- Progressive Web App (PWA) support with proper favicon configuration

## Deployment

The application can be deployed to [Vercel](https://vercel.com) or any other platform that supports Next.js applications.

For Vercel deployment:
1. Push your code to a Git repository
2. Import the project in Vercel
3. Vercel will automatically detect it's a Next.js app and configure the build settings

## Learn More

To learn more about the technologies used in this project:

- [Next.js Documentation](https://nextjs.org/docs)
- [TypeScript Documentation](https://www.typescriptlang.org/docs)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Geist Font Documentation](https://vercel.com/font)
